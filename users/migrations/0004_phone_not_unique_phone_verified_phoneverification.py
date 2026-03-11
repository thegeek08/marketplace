"""
Migration 0004:
- Supprime la contrainte unique sur phone (un numéro peut avoir 2 comptes: client + vendeur)
- Ajoute unique_together = [('phone', 'role')] pour garantir unicité par rôle
- Ajoute le champ phone_verified sur User
- Crée le modèle PhoneVerification pour la validation SMS
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_user_email'),
    ]

    operations = [
        # 1. Retirer unique=True sur phone
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.CharField(max_length=20),
        ),
        # 2. Ajouter phone_verified
        migrations.AddField(
            model_name='user',
            name='phone_verified',
            field=models.BooleanField(default=False),
        ),
        # 3. Contrainte unique par (phone, role)
        migrations.AlterUniqueTogether(
            name='user',
            unique_together={('phone', 'role')},
        ),
        # 4. Créer PhoneVerification
        migrations.CreateModel(
            name='PhoneVerification',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('code', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_used', models.BooleanField(default=False)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='verifications',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]
