from .models import Notification


def create_notification(user, type, message, url=''):
    """Crée une notification pour un utilisateur."""
    Notification.objects.create(user=user, type=type, message=message, url=url)
