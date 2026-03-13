import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Crée un superuser admin depuis les variables d'environnement ADMIN_PHONE et ADMIN_PASSWORD"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        phone = os.environ.get('ADMIN_PHONE')
        password = os.environ.get('ADMIN_PASSWORD')

        if not phone or not password:
            self.stdout.write(self.style.WARNING(
                'ADMIN_PHONE ou ADMIN_PASSWORD non définis — superuser non créé.'
            ))
            return

        if User.objects.filter(phone=phone, is_staff=True).exists():
            self.stdout.write(self.style.SUCCESS(
                f'Superuser {phone} existe déjà — rien à faire.'
            ))
            return

        user = User.objects.create_superuser(phone=phone, password=password)
        user.phone_verified = True
        user.is_active = True
        user.profile_completed = True
        user.save()
        self.stdout.write(self.style.SUCCESS(f'Superuser {phone} créé avec succès.'))
