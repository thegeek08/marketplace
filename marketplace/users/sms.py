"""
Utilitaire d'envoi de SMS via Twilio.
Si TWILIO_ACCOUNT_SID n'est pas configuré, la vérification SMS est désactivée :
l'inscription et la connexion fonctionnent sans SMS (compte activé directement).
Quand les clés Twilio seront ajoutées (ex: Render), la vérification s'active automatiquement.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def twilio_configured() -> bool:
    """Retourne True si les credentials Twilio sont tous définis."""
    return all([
        getattr(settings, 'TWILIO_ACCOUNT_SID', ''),
        getattr(settings, 'TWILIO_AUTH_TOKEN', ''),
        getattr(settings, 'TWILIO_PHONE_NUMBER', ''),
    ])


def send_verification_sms(phone: str, code: str) -> bool:
    """
    Envoie un SMS de vérification au numéro indiqué.
    Retourne True si le SMS a été envoyé, False sinon.
    """
    if not twilio_configured():
        logger.info(f"[SMS désactivé] Code pour {phone} : {code}")
        return False

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=f"Marketplace Sénégal — Votre code de vérification : {code}. Valable 10 minutes.",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone,
        )
        return True
    except Exception as exc:
        logger.error(f"Erreur envoi SMS Twilio vers {phone}: {exc}")
        return False
