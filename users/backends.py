from django.contrib.auth import get_user_model

User = get_user_model()


class PhoneRoleBackend:
    """
    Authentification par numéro de téléphone + rôle + mot de passe.
    Nécessaire car un même numéro peut avoir 2 comptes (client et vendeur).
    """

    def authenticate(self, request, phone=None, password=None, role=None, **kwargs):
        if not phone or not password:
            return None
        try:
            if role:
                user = User.objects.get(phone=phone, role=role)
            else:
                # Compatibilité: si un seul compte pour ce numéro
                users = User.objects.filter(phone=phone)
                if users.count() == 1:
                    user = users.first()
                else:
                    return None
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def user_can_authenticate(self, user):
        return getattr(user, 'is_active', False)

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
