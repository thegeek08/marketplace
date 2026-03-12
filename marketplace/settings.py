from pathlib import Path
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ──────────────────────────────────────────────
# SECURITE
# ──────────────────────────────────────────────

SECRET_KEY = config('SECRET_KEY')  # Obligatoire — aucun fallback pour éviter une clé prévisible en production

DEBUG = config('DEBUG', default=False, cast=bool)

# Version de l'application — incrémenter à chaque déploiement pour forcer le rechargement du cache PWA
APP_VERSION = config('APP_VERSION', default='v2')

# URL de production Render — utilisée par le management command keep_alive
RENDER_URL = config('RENDER_URL', default='https://marketplace-q807.onrender.com/ping/')

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
    cast=Csv()
)

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:8000',
    cast=Csv()
)

# ──────────────────────────────────────────────
# APPLICATIONS
# ──────────────────────────────────────────────

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary_storage',  # doit être avant les apps custom pour media
    'cloudinary',
    'users',
    'products',
    'cart',
    'orders',
    'messaging',
    'favorites',
    'notifications',
]

# ──────────────────────────────────────────────
# MIDDLEWARE (whitenoise juste après security)
# ──────────────────────────────────────────────

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # sert les fichiers statiques en production
    'users.middleware.SecurityHeadersMiddleware',  # CSP, Referrer-Policy, Permissions-Policy
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'users.middleware.ProfileCompletionMiddleware',  # force complétion profil après inscription
]

ROOT_URLCONF = 'marketplace.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'marketplace' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.notifications_unread',
            ],
        },
    },
]

WSGI_APPLICATION = 'marketplace.wsgi.application'

# ──────────────────────────────────────────────
# BASE DE DONNEES
# SQLite en local, PostgreSQL sur Railway via DATABASE_URL
# ──────────────────────────────────────────────

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# ──────────────────────────────────────────────
# AUTHENTIFICATION
# ──────────────────────────────────────────────

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/users/dashboard/'
LOGOUT_REDIRECT_URL = '/users/login/'

# ──────────────────────────────────────────────
# AUTHENTICATION BACKENDS
# PhoneRoleBackend gère 2 comptes par numéro (client + vendeur)
# ──────────────────────────────────────────────

AUTHENTICATION_BACKENDS = [
    'users.backends.PhoneRoleBackend',
]

# ──────────────────────────────────────────────
# TWILIO SMS
# Configurer dans .env :
#   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
#   TWILIO_AUTH_TOKEN=your_auth_token
#   TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
# Si non configuré : le code s'affiche dans la console (mode dev)
# ──────────────────────────────────────────────

TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default='')

# ──────────────────────────────────────────────
# INTERNATIONALISATION
# ──────────────────────────────────────────────

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Dakar'
USE_I18N = True
USE_TZ = True

# ──────────────────────────────────────────────
# FICHIERS STATIQUES (whitenoise + collectstatic)
# ──────────────────────────────────────────────

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # dossier de collectstatic en production

# Dossier static local (dev)
_static_dir = BASE_DIR / 'static'
STATICFILES_DIRS = [_static_dir] if _static_dir.exists() else []

# ──────────────────────────────────────────────
# CLOUDINARY — stockage persistant des media
# En local : stockage fichier classique (MEDIA_ROOT)
# En production : Cloudinary si CLOUDINARY_CLOUD_NAME est défini
# ──────────────────────────────────────────────

CLOUDINARY_CLOUD_NAME = config('CLOUDINARY_CLOUD_NAME', default='')

if CLOUDINARY_CLOUD_NAME:
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
        'API_KEY': config('CLOUDINARY_API_KEY', default=''),
        'API_SECRET': config('CLOUDINARY_API_SECRET', default=''),
    }
    _media_backend = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    MEDIA_URL = f'https://res.cloudinary.com/{CLOUDINARY_CLOUD_NAME}/'
else:
    _media_backend = 'django.core.files.storage.FileSystemStorage'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# WhiteNoise pour les statiques, Cloudinary (ou local) pour les media
STORAGES = {
    'default': {
        'BACKEND': _media_backend,
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ──────────────────────────────────────────────
# EMAIL (Gmail)
# ──────────────────────────────────────────────

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='Marketplace <noreply@marketplace.sn>')
ADMIN_EMAIL = config('ADMIN_EMAIL', default='')  # Email de l'admin pour les signalements

# ──────────────────────────────────────────────
# SECURITE HTTPS (actif hors DEBUG)
# ──────────────────────────────────────────────

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # HSTS : force HTTPS pendant 1 an, inclut les sous-domaines
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Empêche le MIME sniffing
    SECURE_CONTENT_TYPE_NOSNIFF = True

# ──────────────────────────────────────────────
# LIMITE TAILLE DES UPLOADS
# ──────────────────────────────────────────────

# 5 Mo max pour les images (avatars, produits)
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 Mo
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 Mo

# ──────────────────────────────────────────────
# SESSIONS
# ──────────────────────────────────────────────

SESSION_COOKIE_AGE            = 86400   # 24 h en secondes
SESSION_SAVE_EVERY_REQUEST    = True    # renouvelle le TTL à chaque requête
SESSION_EXPIRE_AT_BROWSER_CLOSE = False # persiste après fermeture du navigateur
SESSION_COOKIE_HTTPONLY       = True    # inaccessible au JS (XSS mitigation)
SESSION_COOKIE_SAMESITE       = 'Lax'  # protection CSRF cross-site

# ──────────────────────────────────────────────
# CACHE (utilisé par le rate-limiter brute force)
# En production, remplace par Redis via REDIS_URL
# ──────────────────────────────────────────────

REDIS_URL = config('REDIS_URL', default='')

if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'marketplace-cache',
        }
    }

# ──────────────────────────────────────────────
# PROTECTION BRUTE FORCE
# ──────────────────────────────────────────────

BRUTE_FORCE_MAX_ATTEMPTS = 5     # tentatives avant blocage
BRUTE_FORCE_LOCKOUT_SECS = 900   # 15 minutes

# ──────────────────────────────────────────────
# LOGS DE SECURITE ET D'AUDIT
# ──────────────────────────────────────────────

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '[%(asctime)s] %(levelname)s %(name)s | %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s %(module)s | %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 5 * 1024 * 1024,  # 5 Mo
            'backupCount': 5,
            'formatter': 'security',
        },
        'audit_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'audit.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'security',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'audit': {
            'handlers': ['console', 'audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
