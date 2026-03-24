import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Réinitialise le mot de passe d'un compte via RESET_PHONE et RESET_PASSWORD"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        phone = os.environ.get('RESET_PHONE')
        password = os.environ.get('RESET_PASSWORD')

        if not phone or not password:
            self.stdout.write(self.style.WARNING(
                'RESET_PHONE ou RESET_PASSWORD non définis — rien à faire.'
            ))
            return

        users = User.objects.filter(phone=phone)
        if not users.exists():
            self.stdout.write(self.style.ERROR(f'Aucun compte trouvé pour {phone}.'))
            return

        for user in users:
            user.set_password(password)
            user.save(update_fields=['password'])
            self.stdout.write(self.style.SUCCESS(
                f'Mot de passe réinitialisé pour {phone} (role={user.role}).'
            ))
