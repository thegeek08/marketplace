"""
Management command : keep_alive
===============================
Ping le serveur Render toutes les 10 minutes pour l'empêcher de se mettre
en veille (sleep) sur le plan gratuit.

Usage :
    python manage.py keep_alive              # ping en boucle infinie
    python manage.py keep_alive --once       # ping unique (pour cron externe)
    python manage.py keep_alive --interval 5 # ping toutes les 5 minutes
"""

import time
import urllib.request
import urllib.error
from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings


RENDER_URL = getattr(settings, 'RENDER_URL', 'https://marketplace-q807.onrender.com/ping/')


class Command(BaseCommand):
    help = "Ping le serveur Render toutes les N minutes pour éviter la mise en veille."

    def add_arguments(self, parser):
        parser.add_argument(
            '--once',
            action='store_true',
            help='Effectue un seul ping puis quitte.',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=10,
            help='Intervalle en minutes entre chaque ping (défaut : 10).',
        )

    def handle(self, *args, **options):
        once = options['once']
        interval = options['interval']
        url = RENDER_URL

        self.stdout.write(f"[keep_alive] URL cible : {url}")

        if once:
            self._ping(url)
            return

        self.stdout.write(f"[keep_alive] Ping toutes les {interval} minutes. Ctrl+C pour arrêter.\n")
        while True:
            self._ping(url)
            time.sleep(interval * 60)

    def _ping(self, url):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                status = resp.status
            self.stdout.write(self.style.SUCCESS(f"[{now}] OK  {status}  {url}"))
        except urllib.error.HTTPError as e:
            self.stdout.write(self.style.WARNING(f"[{now}] HTTP {e.code}  {url}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[{now}] ERREUR  {url}  — {e}"))
