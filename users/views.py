import logging

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Sum
from django_ratelimit.decorators import ratelimit

from .forms import RegisterForm, LoginForm, VerifyCodeForm, CompleteProfileForm, ProfileForm, ChangePasswordForm, DeleteAccountForm
from .models import PhoneVerification
from .sms import send_verification_sms, twilio_configured
from .security import (
    is_locked_ip, is_locked_phone, record_failed_attempt,
    reset_attempts, get_client_ip, remaining_lockout, LOCKOUT_SECS,
)

security_logger = logging.getLogger('security')
audit_logger    = logging.getLogger('audit')


# ──────────────────────────────────────────────────────────
# INSCRIPTION avec vérification SMS
# ──────────────────────────────────────────────────────────

@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            if twilio_configured():
                # ── Mode SMS actif : compte inactif jusqu'à vérification ──
                user.is_active = False
                user.phone_verified = False
                user.save()

                code = PhoneVerification.generate_code()
                PhoneVerification.objects.create(user=user, code=code)
                send_verification_sms(user.phone, code)

                request.session['pending_user_id'] = user.pk
                messages.info(
                    request,
                    f"Un code de vérification a été envoyé au {user.phone}. "
                    "Entrez-le ci-dessous pour activer votre compte."
                )
                audit_logger.info(
                    'REGISTER | phone=%s role=%s ip=%s',
                    user.phone, user.role, get_client_ip(request)
                )
                return redirect("verify_phone")
            else:
                # ── Mode sans SMS : compte activé directement ──
                user.is_active = True
                user.phone_verified = False  # sera True quand Twilio activé
                user.save()
                login(request, user, backend='users.backends.PhoneRoleBackend')
                audit_logger.info(
                    'REGISTER | phone=%s role=%s ip=%s',
                    user.phone, user.role, get_client_ip(request)
                )
                messages.success(request, "Compte créé ! Complétez votre profil pour continuer.")
                return redirect("complete_profile")
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})


# ──────────────────────────────────────────────────────────
# VÉRIFICATION SMS
# ──────────────────────────────────────────────────────────

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def verify_phone(request):
    pending_id = request.session.get('pending_user_id')
    if not pending_id:
        messages.error(request, "Aucun compte en attente de vérification.")
        return redirect("register")

    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(pk=pending_id)
    except User.DoesNotExist:
        messages.error(request, "Compte introuvable.")
        return redirect("register")

    if request.method == "POST":
        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            entered_code = form.cleaned_data['code'].strip()

            # Chercher le dernier code non utilisé
            verification = (
                PhoneVerification.objects
                .filter(user=user, is_used=False)
                .order_by('-created_at')
                .first()
            )

            if verification is None:
                messages.error(request, "Aucun code de vérification trouvé. Réinscrivez-vous.")
                return redirect("register")

            if not verification.is_valid():
                messages.error(
                    request,
                    "Ce code a expiré (10 minutes). "
                    "<a href='javascript:history.back()'>Renvoyer un code</a>."
                )
            elif verification.code != entered_code:
                messages.error(request, "Code incorrect. Vérifiez et réessayez.")
            else:
                # Code valide → activer le compte
                verification.is_used = True
                verification.save()

                user.is_active = True
                user.phone_verified = True
                user.save()

                # Nettoyer la session
                del request.session['pending_user_id']

                # Connecter l'utilisateur
                login(request, user, backend='users.backends.PhoneRoleBackend')
                messages.success(request, "Numéro vérifié ! Complétez votre profil pour continuer.")
                return redirect("complete_profile")
    else:
        form = VerifyCodeForm()

    return render(request, "users/verify.html", {"form": form, "phone": user.phone})


@ratelimit(key='ip', rate='3/h', method='ALL', block=True)
def resend_verification(request):
    """Renvoie un nouveau code SMS."""
    pending_id = request.session.get('pending_user_id')
    if not pending_id:
        return redirect("register")

    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(pk=pending_id)
    except User.DoesNotExist:
        return redirect("register")

    # Invalider les anciens codes
    PhoneVerification.objects.filter(user=user, is_used=False).update(is_used=True)

    # Générer et envoyer un nouveau code
    code = PhoneVerification.generate_code()
    PhoneVerification.objects.create(user=user, code=code)
    sms_sent = send_verification_sms(user.phone, code)

    if sms_sent:
        messages.success(request, "Un nouveau code a été envoyé.")
    else:
        messages.warning(request, "SMS non envoyé (mode dev) — consultez la console.")

    return redirect("verify_phone")


# ──────────────────────────────────────────────────────────
# CONNEXION
# ──────────────────────────────────────────────────────────

@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def login_view(request):
    ip = get_client_ip(request)

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            password = form.cleaned_data['password']
            role = form.cleaned_data['role']

            # ── Vérification blocage brute force ──────────────────────────
            if is_locked_ip(ip) or is_locked_phone(phone, role):
                ttl = remaining_lockout(ip, phone, role)
                minutes = max(1, ttl // 60)
                security_logger.warning(
                    'LOGIN_BLOCKED | phone=%s role=%s ip=%s ttl=%ds',
                    phone, role, ip, ttl
                )
                messages.error(
                    request,
                    f"Trop de tentatives échouées. Compte temporairement bloqué. "
                    f"Réessayez dans {minutes} minute(s)."
                )
                return render(request, "users/login.html", {"form": form})

            user = authenticate(request, phone=phone, password=password, role=role)

            # Diagnostic : compte existant mais mot de passe inutilisable
            if user is None:
                from django.contrib.auth import get_user_model
                _User = get_user_model()
                _accounts = _User.objects.filter(phone=phone)
                if _accounts.exists() and all(not u.has_usable_password() for u in _accounts):
                    messages.error(
                        request,
                        "Ce compte n'a pas de mot de passe défini. "
                        "Utilisez « Mot de passe oublié » pour en créer un."
                    )
                    return render(request, "users/login.html", {"form": form})

            if user is not None:
                # Connexion réussie → réinitialiser les compteurs
                # Utiliser le vrai rôle du compte trouvé (peut différer du rôle sélectionné)
                reset_attempts(ip, phone, user.role)

                if not user.phone_verified and twilio_configured():
                    request.session['pending_user_id'] = user.pk
                    PhoneVerification.objects.filter(user=user, is_used=False).update(is_used=True)
                    code = PhoneVerification.generate_code()
                    PhoneVerification.objects.create(user=user, code=code)
                    send_verification_sms(user.phone, code)
                    messages.warning(
                        request,
                        "Votre compte n'est pas encore vérifié. "
                        "Un nouveau code a été envoyé."
                    )
                    return redirect("verify_phone")

                login(request, user, backend='users.backends.PhoneRoleBackend')
                audit_logger.info(
                    'LOGIN_SUCCESS | user_id=%d phone=%s role=%s ip=%s',
                    user.pk, phone, user.role, ip
                )
                messages.success(request, f"Connexion réussie en tant que {user.get_role_display()} !")
                if not user.profile_completed:
                    return redirect("complete_profile")
                return redirect("dashboard")

            else:
                # Échec → enregistrer la tentative
                count = record_failed_attempt(ip, phone, role)
                remaining = max(0, 5 - count)
                security_logger.warning(
                    'LOGIN_FAILED | phone=%s role=%s ip=%s attempts=%d',
                    phone, role, ip, count
                )
                if remaining > 0:
                    messages.error(
                        request,
                        f"Numéro de téléphone ou mot de passe incorrect. "
                        f"({remaining} tentative(s) restante(s) avant blocage)"
                    )
                else:
                    messages.error(
                        request,
                        "Compte bloqué après trop d'échecs. "
                        f"Réessayez dans {LOCKOUT_SECS // 60} minutes."
                    )
    else:
        form = LoginForm()
    return render(request, "users/login.html", {"form": form})


# ──────────────────────────────────────────────────────────
# DÉCONNEXION
# ──────────────────────────────────────────────────────────

@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Vous êtes déconnecté")
    return redirect("login")


# ──────────────────────────────────────────────────────────
# COMPLÉTION DE PROFIL (obligatoire après inscription)
# ──────────────────────────────────────────────────────────

@login_required
def complete_profile(request):
    # Si déjà complété, aller directement au dashboard
    if request.user.profile_completed:
        return redirect("dashboard")

    if request.method == "POST":
        form = CompleteProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.profile_completed = True
            user.save()
            messages.success(request, f"Profil complété ! Bienvenue {user.nom} 🎉")
            return redirect("dashboard")
    else:
        form = CompleteProfileForm(instance=request.user)

    return render(request, "users/complete_profile.html", {"form": form})


# ──────────────────────────────────────────────────────────
# TABLEAU DE BORD
# ──────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    user = request.user
    context = {'user': user}

    if user.role == 'client':
        from orders.models import Order
        from favorites.models import Favorite
        from messaging.models import Conversation

        orders = Order.objects.filter(client=user)
        recent_orders = orders[:5]
        favorites_count = Favorite.objects.filter(user=user).count()
        conversations = Conversation.objects.filter(client=user)
        unread_messages = sum(c.unread_count(user) for c in conversations)

        context.update({
            'orders_count': orders.count(),
            'orders_en_attente': orders.filter(status='en_attente').count(),
            'orders_en_livraison': orders.filter(status='en_livraison').count(),
            'recent_orders': recent_orders,
            'favorites_count': favorites_count,
            'unread_messages': unread_messages,
            'conversations_count': conversations.count(),
        })

    elif user.role == 'vendeur':
        from products.models import Product
        from orders.models import Order, OrderItem
        from messaging.models import Conversation

        products = Product.objects.filter(seller=user)
        # Commandes contenant des produits du vendeur
        vendor_order_items = OrderItem.objects.filter(product__seller=user)
        vendor_order_ids = vendor_order_items.values_list('order_id', flat=True).distinct()
        orders = Order.objects.filter(id__in=vendor_order_ids)
        recent_orders = orders[:5]

        # Revenus (commandes livrées)
        revenue_data = vendor_order_items.filter(
            order__status='livree'
        ).aggregate(total=Sum('price'))
        revenue = revenue_data['total'] or 0

        conversations = Conversation.objects.filter(vendeur=user)
        unread_messages = sum(c.unread_count(user) for c in conversations)

        context.update({
            'products_count': products.count(),
            'products_actifs': products.count(),
            'orders_count': orders.count(),
            'orders_en_attente': orders.filter(status='en_attente').count(),
            'recent_orders': recent_orders,
            'revenue': revenue,
            'unread_messages': unread_messages,
            'conversations_count': conversations.count(),
        })

    return render(request, "users/dashboard.html", context)


# ──────────────────────────────────────────────────────────
# PROFIL
# ──────────────────────────────────────────────────────────

@login_required
def profile(request):
    profile_form = ProfileForm(instance=request.user)
    password_form = ChangePasswordForm()
    delete_form = DeleteAccountForm()

    if request.method == "POST":
        action = request.POST.get('action')

        if action == 'update_profile':
            profile_form = ProfileForm(
                request.POST, request.FILES, instance=request.user
            )
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profil mis à jour avec succès !")
                return redirect("profile")

        elif action == 'change_password':
            password_form = ChangePasswordForm(request.POST)
            if password_form.is_valid():
                old_password = password_form.cleaned_data['old_password']
                new_password = password_form.cleaned_data['new_password1']
                if request.user.check_password(old_password):
                    try:
                        validate_password(new_password, request.user)
                    except ValidationError as e:
                        for error in e.messages:
                            messages.error(request, error)
                    else:
                        request.user.set_password(new_password)
                        request.user.save()
                        update_session_auth_hash(request, request.user)
                        messages.success(request, "Mot de passe changé avec succès !")
                        return redirect("profile")
                else:
                    messages.error(request, "Ancien mot de passe incorrect")

        elif action == 'delete_account':
            delete_form = DeleteAccountForm(request.POST)
            if delete_form.is_valid():
                if request.user.check_password(delete_form.cleaned_data['password']):
                    request.user.delete()
                    logout(request)
                    messages.info(request, "Votre compte a été supprimé")
                    return redirect("register")
                else:
                    messages.error(request, "Mot de passe incorrect. Suppression annulée.")

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
        'delete_form': delete_form,
    }
    return render(request, "users/profile.html", context)
