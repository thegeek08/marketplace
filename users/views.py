from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from .forms import RegisterForm, LoginForm, VerifyCodeForm, CompleteProfileForm, ProfileForm, ChangePasswordForm
from .models import PhoneVerification
from .sms import send_verification_sms, twilio_configured


# ──────────────────────────────────────────────────────────
# INSCRIPTION avec vérification SMS
# ──────────────────────────────────────────────────────────

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
                return redirect("verify_phone")
            else:
                # ── Mode sans SMS : compte activé directement ──
                user.is_active = True
                user.phone_verified = False  # sera True quand Twilio activé
                user.save()
                login(request, user, backend='users.backends.PhoneRoleBackend')
                messages.success(request, "Compte créé ! Complétez votre profil pour continuer.")
                return redirect("complete_profile")
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})


# ──────────────────────────────────────────────────────────
# VÉRIFICATION SMS
# ──────────────────────────────────────────────────────────

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

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            password = form.cleaned_data['password']
            role = form.cleaned_data['role']
            user = authenticate(request, phone=phone, password=password, role=role)
            if user is not None:
                if not user.phone_verified and twilio_configured():
                    # Compte non vérifié et Twilio actif → renvoyer vers vérification
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
                login(request, user)
                messages.success(request, "Connexion réussie !")
                if not user.profile_completed:
                    return redirect("complete_profile")
                return redirect("dashboard")
            else:
                messages.error(request, "Téléphone, rôle ou mot de passe incorrect.")
    else:
        form = LoginForm()
    return render(request, "users/login.html", {"form": form})


# ──────────────────────────────────────────────────────────
# DÉCONNEXION
# ──────────────────────────────────────────────────────────

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
                if request.user.check_password(old_password):
                    request.user.set_password(
                        password_form.cleaned_data['new_password1']
                    )
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    messages.success(request, "Mot de passe changé avec succès !")
                    return redirect("profile")
                else:
                    messages.error(request, "Ancien mot de passe incorrect")

        elif action == 'delete_account':
            request.user.delete()
            logout(request)
            messages.info(request, "Votre compte a été supprimé")
            return redirect("register")

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, "users/profile.html", context)
