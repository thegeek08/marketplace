"""
Utilitaire d'envoi de SMS via Twilio.
Si les credentials Twilio ne sont pas configurés, le code est affiché en console (dev).
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def send_verification_sms(phone: str, code: str) -> bool:
    """
    Envoie un SMS de vérification au numéro indiqué.
    Retourne True si le SMS a été envoyé, False sinon.
    """
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '')

    if not all([account_sid, auth_token, from_number]):
        # Mode développement : afficher le code dans la console
        logger.warning(
            f"[SMS DEV] Code de vérification pour {phone} : {code}"
        )
        print(f"\n{'='*50}")
        print(f"[SMS DEV] Numéro: {phone} — Code: {code}")
        print(f"{'='*50}\n")
        return False  # False = SMS pas envoyé (mode dev)

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        client.messages.create(
            body=f"Marketplace Sénégal — Votre code de vérification : {code}. Valable 10 minutes.",
            from_=from_number,
            to=phone,
        )
        return True
    except Exception as exc:
        logger.error(f"Erreur envoi SMS Twilio vers {phone}: {exc}")
        return False
