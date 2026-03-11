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

        # ── Tentative 1 : correspondance exacte phone + rôle ──────────────────
        if role:
            try:
                user = User.objects.get(phone=phone, role=role)
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
            except User.DoesNotExist:
                pass  # rôle incorrect → on essaie le fallback

        # ── Tentative 2 : fallback si un seul compte pour ce numéro ───────────
        # (couvre le cas où l'utilisateur a oublié de changer le sélecteur de rôle)
        accounts = list(User.objects.filter(phone=phone))
        if len(accounts) == 1:
            user = accounts[0]
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

        # ── Tentative 3 : deux comptes → chercher celui dont le mdp correspond ─
        elif len(accounts) == 2:
            for user in accounts:
                if user.check_password(password) and self.user_can_authenticate(user):
                    # Ambiguïté résolue par le mot de passe uniquement
                    # (acceptable si les deux comptes ont des mots de passe différents)
                    return user

        return None

    def user_can_authenticate(self, user):
        return getattr(user, 'is_active', False)

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
