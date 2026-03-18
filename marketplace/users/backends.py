import logging
from django.contrib.auth import get_user_model

User = get_user_model()
security_logger = logging.getLogger('security')


class PhoneRoleBackend:
    """
    Authentification par numéro de téléphone + rôle + mot de passe.
    Nécessaire car un même numéro peut avoir 2 comptes (client et vendeur).

    3 tentatives en cascade :
      1. Correspondance exacte phone + rôle sélectionné
      2. Fallback si un seul compte pour ce numéro (rôle ignoré)
      3. Deux comptes → celui dont le mot de passe correspond
    """

    def authenticate(self, request, phone=None, password=None, role=None, **kwargs):
        # L'admin Django passe 'username' au lieu de 'phone' → on accepte les deux
        phone = phone or kwargs.get('username')
        if not phone or not password:
            return None

        # ── Tentative 1 : correspondance exacte phone + rôle ──────────────────
        if role:
            try:
                user = User.objects.get(phone=phone, role=role)
                if self._check_user(user, password):
                    return user
                # Mot de passe incorrect pour ce compte exact,
                # mais on continue vers Tentative 2/3 (peut-être l'autre compte)
            except User.DoesNotExist:
                pass  # rôle incorrect → fallback

        # ── Tentative 2 : fallback si un seul compte pour ce numéro ───────────
        # Couvre le cas où l'utilisateur oublie de changer le sélecteur de rôle
        accounts = list(User.objects.filter(phone=phone))

        if len(accounts) == 0:
            security_logger.warning(
                'AUTH_FAIL | phone=%s role=%s reason=phone_not_found',
                phone, role
            )
            return None

        if len(accounts) == 1:
            user = accounts[0]
            if self._check_user(user, password):
                return user
            # Log la vraie raison pour le débogage
            if not self.user_can_authenticate(user):
                security_logger.warning(
                    'AUTH_FAIL | phone=%s role=%s reason=account_inactive user_id=%d',
                    phone, role, user.pk
                )
            elif not user.has_usable_password():
                security_logger.warning(
                    'AUTH_FAIL | phone=%s role=%s reason=no_usable_password user_id=%d '
                    '(compte sans mot de passe - utiliser "Mot de passe oublié")',
                    phone, role, user.pk
                )
            else:
                security_logger.warning(
                    'AUTH_FAIL | phone=%s role=%s reason=wrong_password user_id=%d',
                    phone, role, user.pk
                )
            return None

        # ── Tentative 3 : deux comptes → celui dont le mot de passe correspond ─
        for user in accounts:
            if self._check_user(user, password):
                return user

        security_logger.warning(
            'AUTH_FAIL | phone=%s role=%s reason=wrong_password_both_accounts',
            phone, role
        )
        return None

    def _check_user(self, user, password):
        """Vérifie mot de passe + compte actif."""
        return (
            self.user_can_authenticate(user)
            and user.has_usable_password()
            and user.check_password(password)
        )

    def user_can_authenticate(self, user):
        return getattr(user, 'is_active', False)

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
