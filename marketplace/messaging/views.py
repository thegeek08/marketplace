import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings as django_settings
from .models import Conversation, Message, UserBlock, UserReport
from products.models import Product

audit_logger = logging.getLogger('audit')


@login_required
def conversation_list(request):
    user = request.user
    if user.role == 'client':
        conversations = Conversation.objects.filter(client=user)
    else:
        conversations = Conversation.objects.filter(vendeur=user)
    return render(request, 'messaging/conversation_list.html', {
        'conversations': conversations
    })


@login_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)
    user = request.user

    if user != conversation.client and user != conversation.vendeur:
        return redirect('conversation_list')

    # L'autre participant
    other_user = conversation.vendeur if user == conversation.client else conversation.client

    # Vérifier si l'utilisateur courant a bloqué l'autre
    is_blocked_by_me = UserBlock.objects.filter(blocker=user, blocked=other_user).exists()
    # Vérifier si l'autre a bloqué l'utilisateur courant
    am_i_blocked = UserBlock.objects.filter(blocker=other_user, blocked=user).exists()

    # Marquer les messages comme lus
    conversation.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)

    if request.method == 'POST':
        if am_i_blocked or is_blocked_by_me:
            messages.error(request, "Vous ne pouvez pas envoyer de message : l'utilisateur est bloqué.")
            return redirect('conversation_detail', pk=pk)

        content = request.POST.get('content', '').strip()
        if len(content) > 2000:
            messages.error(request, "Le message ne peut pas dépasser 2000 caractères.")
            return redirect('conversation_detail', pk=pk)
        if content:
            msg = Message.objects.create(
                conversation=conversation,
                sender=user,
                content=content
            )
            conversation.save()  # met à jour updated_at

            # Notifier le destinataire
            from notifications.utils import create_notification
            create_notification(
                user=other_user,
                type='message',
                message=f"Nouveau message de {user.nom or user.phone} : {content[:60]}{'...' if len(content) > 60 else ''}",
                url=f'/messaging/{conversation.pk}/'
            )

        return redirect('conversation_detail', pk=pk)

    return render(request, 'messaging/conversation_detail.html', {
        'conversation': conversation,
        'messages_list': conversation.messages.all(),
        'other_user': other_user,
        'is_blocked_by_me': is_blocked_by_me,
        'am_i_blocked': am_i_blocked,
        'report_reasons': UserReport.REASON_CHOICES,
    })


@login_required
def start_conversation(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    user = request.user

    if user.role != 'client':
        messages.error(request, "Seuls les clients peuvent contacter un vendeur")
        return redirect('product_detail', pk=product_pk)

    if user == product.seller:
        messages.error(request, "Vous ne pouvez pas vous contacter vous-même")
        return redirect('product_detail', pk=product_pk)

    conversation, created = Conversation.objects.get_or_create(
        client=user,
        vendeur=product.seller,
        product=product
    )

    return redirect('conversation_detail', pk=conversation.pk)


# ──────────────────────────────────────────────
# BLOQUER un utilisateur
# ──────────────────────────────────────────────

@login_required
def block_user(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)
    user = request.user

    if user != conversation.client and user != conversation.vendeur:
        return redirect('conversation_list')

    other_user = conversation.vendeur if user == conversation.client else conversation.client

    already_blocked = UserBlock.objects.filter(blocker=user, blocked=other_user).exists()

    if already_blocked:
        # Débloquer
        UserBlock.objects.filter(blocker=user, blocked=other_user).delete()
        messages.success(request, f"{other_user.nom or other_user.phone} a été débloqué.")
    else:
        UserBlock.objects.get_or_create(blocker=user, blocked=other_user)
        messages.warning(request, f"{other_user.nom or other_user.phone} a été bloqué. Vous ne recevrez plus ses messages.")

    return redirect('conversation_detail', pk=pk)


# ──────────────────────────────────────────────
# SIGNALER un utilisateur
# ──────────────────────────────────────────────

@login_required
def report_user(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)
    user = request.user

    if user != conversation.client and user != conversation.vendeur:
        return redirect('conversation_list')

    other_user = conversation.vendeur if user == conversation.client else conversation.client

    if request.method == 'POST':
        reason = request.POST.get('reason', 'autre')
        details = request.POST.get('details', '').strip()

        report = UserReport.objects.create(
            reporter=user,
            reported=other_user,
            reason=reason,
            details=details
        )

        # Envoyer un email à l'admin
        reason_label = dict(UserReport.REASON_CHOICES).get(reason, reason)
        subject = f"[Marketplace] Signalement — {other_user.nom or other_user.phone}"
        body = (
            f"Un utilisateur a été signalé sur la marketplace.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Signalé par   : {user.nom or user.phone} (ID {user.pk})\n"
            f"Utilisateur   : {other_user.nom or other_user.phone} (ID {other_user.pk})\n"
            f"Téléphone     : {other_user.phone}\n"
            f"Email         : {other_user.email or 'Non renseigné'}\n"
            f"Rôle          : {other_user.role}\n"
            f"Motif         : {reason_label}\n"
            f"Détails       : {details or 'Aucun détail fourni'}\n"
            f"Conversation  : #{conversation.pk}\n"
            f"Date          : {report.created_at.strftime('%d/%m/%Y %H:%M')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Connecte-toi à l'admin pour décider : bannir ou suspendre."
        )

        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[django_settings.ADMIN_EMAIL],
                fail_silently=False,
            )
        except Exception:
            pass  # Le signalement est enregistré même si l'email échoue

        audit_logger.warning(
            'USER_REPORT | reporter_id=%d reported_id=%d reason=%s conversation_id=%d',
            user.pk, other_user.pk, reason, conversation.pk
        )
        messages.success(request, "Signalement envoyé. Nous examinerons la situation rapidement.")

    return redirect('conversation_detail', pk=pk)
