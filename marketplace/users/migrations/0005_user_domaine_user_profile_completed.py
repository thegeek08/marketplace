from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_phone_not_unique_phone_verified_phoneverification'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='domaine',
            field=models.CharField(
                blank=True,
                choices=[
                    ('agriculture', 'Agriculture'),
                    ('commerce', 'Commerce'),
                    ('electronique', 'Électronique'),
                    ('mode', 'Mode & Vêtements'),
                    ('beaute', 'Beauté & Cosmétiques'),
                    ('alimentation', 'Alimentation'),
                    ('informatique', 'Informatique'),
                    ('autre', 'Autre'),
                ],
                max_length=30,
                null=True,
                verbose_name="Domaine d'activité",
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='profile_completed',
            field=models.BooleanField(default=False),
        ),
    ]
