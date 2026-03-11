"""
Utilitaires de sécurité : protection brute force par cache Django.

Stratégie double :
  - Par IP  : limite les attaques depuis une même adresse réseau
  - Par téléphone : protège un compte spécifique ciblé depuis IPs multiples

Paramètres configurables via settings :
  BRUTE_FORCE_MAX_ATTEMPTS  (défaut : 5)
  BRUTE_FORCE_LOCKOUT_SECS  (défaut : 900 = 15 min)
"""

import logging
from django.core.cache import cache
from django.conf import settings

security_logger = logging.getLogger('security')

MAX_ATTEMPTS = getattr(settings, 'BRUTE_FORCE_MAX_ATTEMPTS', 5)
LOCKOUT_SECS  = getattr(settings, 'BRUTE_FORCE_LOCKOUT_SECS', 900)   # 15 min


def _ip_key(ip: str) -> str:
    return f'bf_ip:{ip}'


def _phone_key(phone: str, role: str) -> str:
    return f'bf_phone:{phone}:{role}'


# ── Vérification ─────────────────────────────────────────────────────────────

def is_locked_ip(ip: str) -> bool:
    """True si l'IP est bloquée (trop de tentatives)."""
    return (cache.get(_ip_key(ip)) or 0) >= MAX_ATTEMPTS


def is_locked_phone(phone: str, role: str) -> bool:
    """True si le compte (phone+role) est bloqué."""
    return (cache.get(_phone_key(phone, role)) or 0) >= MAX_ATTEMPTS


def remaining_lockout(ip: str, phone: str, role: str) -> int:
    """Retourne le TTL restant (en secondes) du blocage le plus long."""
    ip_ttl    = cache.ttl(_ip_key(ip))         if is_locked_ip(ip)            else 0
    phone_ttl = cache.ttl(_phone_key(phone, role)) if is_locked_phone(phone, role) else 0
    return max(ip_ttl or 0, phone_ttl or 0)


# ── Enregistrement ───────────────────────────────────────────────────────────

def record_failed_attempt(ip: str, phone: str, role: str) -> int:
    """
    Incrémente les compteurs d'échecs.
    Retourne le nombre total de tentatives pour ce compte.
    """
    # Compteur IP
    ip_key = _ip_key(ip)
    ip_count = (cache.get(ip_key) or 0) + 1
    cache.set(ip_key, ip_count, timeout=LOCKOUT_SECS)

    # Compteur compte
    ph_key   = _phone_key(phone, role)
    ph_count = (cache.get(ph_key) or 0) + 1
    cache.set(ph_key, ph_count, timeout=LOCKOUT_SECS)

    if ph_count >= MAX_ATTEMPTS:
        security_logger.warning(
            'BRUTE_FORCE_LOCKOUT | phone=%s role=%s ip=%s attempts=%d',
            phone, role, ip, ph_count
        )

    return ph_count


def reset_attempts(ip: str, phone: str, role: str) -> None:
    """Réinitialise les compteurs après une connexion réussie."""
    cache.delete(_ip_key(ip))
    cache.delete(_phone_key(phone, role))


# ── Helper requête ────────────────────────────────────────────────────────────

def get_client_ip(request) -> str:
    """Retourne l'IP réelle du client (gère les proxies)."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')
