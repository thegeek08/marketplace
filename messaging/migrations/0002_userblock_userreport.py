from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('blocker', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='blocking',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('blocked', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='blocked_by',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Blocage',
                'verbose_name_plural': 'Blocages',
                'unique_together': {('blocker', 'blocked')},
            },
        ),
        migrations.CreateModel(
            name='UserReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(
                    choices=[
                        ('spam', 'Spam'),
                        ('arnaque', 'Arnaque / Fraude'),
                        ('harcelement', 'Harcèlement'),
                        ('contenu_inapproprie', 'Contenu inapproprié'),
                        ('autre', 'Autre'),
                    ],
                    default='autre',
                    max_length=30,
                )),
                ('details', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reporter', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reports_made',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('reported', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reports_received',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Signalement',
                'verbose_name_plural': 'Signalements',
            },
        ),
    ]
