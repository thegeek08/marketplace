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

        # Cherche n'importe quel compte avec ce numéro (is_staff ou non)
        existing = User.objects.filter(phone=phone).order_by('-is_staff').first()
        if existing:
            # Promouvoir le compte existant en superuser + mettre à jour le mdp
            existing.set_password(password)
            existing.is_active = True
            existing.is_staff = True
            existing.is_superuser = True
            existing.phone_verified = True
            existing.profile_completed = True
            existing.save()
            self.stdout.write(self.style.SUCCESS(
                f'Superuser {phone} (role={existing.role}) mis à jour avec succès.'
            ))
            return

        # Aucun compte existant → créer avec role=vendeur
        from django.db import IntegrityError
        try:
            user = User(
                phone=phone, role='vendeur',
                is_staff=True, is_superuser=True,
                is_active=True, phone_verified=True, profile_completed=True,
            )
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser {phone} créé avec succès.'))
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR(f'Erreur création superuser : {e}'))
