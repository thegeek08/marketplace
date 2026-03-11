from django.shortcuts import redirect
from django.conf import settings


# URLs accessibles même si le profil n'est pas complété
ALLOWED_PATHS = {
    '/users/complete-profile/',
    '/users/logout/',
    '/users/login/',
    '/users/register/',
    '/users/verify/',
    '/users/verify/resend/',
    '/gestion-secure-panel/',
}


# ─────────────────────────────────────────────────────────────────────────────
# Middleware : Headers de sécurité HTTP
# Ajoute CSP, X-Frame-Options, Referrer-Policy, Permissions-Policy
# sur chaque réponse.
# ─────────────────────────────────────────────────────────────────────────────

class SecurityHeadersMiddleware:
    """
    Injecte les headers de sécurité HTTP recommandés sur toutes les réponses.
    Compatible avec Django SecurityMiddleware (complémentaire, non redondant).
    """

    CSP = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://res.cloudinary.com; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Content Security Policy
        response['Content-Security-Policy'] = self.CSP

        # Clickjacking — doublon volontaire (au cas où XFrameOptionsMiddleware est absent)
        response.setdefault('X-Frame-Options', 'DENY')

        # MIME sniffing
        response.setdefault('X-Content-Type-Options', 'nosniff')

        # Référent minimal
        response.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')

        # Désactiver des API sensibles du navigateur
        response.setdefault(
            'Permissions-Policy',
            'geolocation=(), microphone=(), camera=(), payment=()'
        )

        return response


class ProfileCompletionMiddleware:
    """
    Redirige vers /users/complete-profile/ si l'utilisateur est connecté
    mais n'a pas encore complété son profil.
    Les routes admin, login, register, verify et complete-profile sont exemptées.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_staff:
            path = request.path
            # Exempter les chemins autorisés et les fichiers statiques/media
            if (
                not request.user.profile_completed
                and not any(path.startswith(p) for p in ALLOWED_PATHS)
                and not path.startswith('/static/')
                and not path.startswith('/media/')
            ):
                return redirect('complete_profile')

        return self.get_response(request)
