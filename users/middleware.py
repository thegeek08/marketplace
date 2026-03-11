from django.shortcuts import redirect
from django.urls import reverse


# URLs accessibles même si le profil n'est pas complété
ALLOWED_PATHS = {
    '/users/complete-profile/',
    '/users/logout/',
    '/users/login/',
    '/users/register/',
    '/users/verify/',
    '/users/verify/resend/',
    '/admin/',
}


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
