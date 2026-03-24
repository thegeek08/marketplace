from django.contrib.auth import get_user_model


def other_account(request):
    """
    Injecte 'other_account' dans tous les templates.
    Si l'utilisateur a un 2e compte (même numéro, rôle différent),
    on expose cet objet pour afficher le bouton de bascule.
    """
    if not request.user.is_authenticated:
        return {'other_account': None}

    User = get_user_model()
    other_role = 'vendeur' if request.user.role == 'client' else 'client'
    try:
        account = User.objects.get(phone=request.user.phone, role=other_role)
        return {'other_account': account}
    except User.DoesNotExist:
        return {'other_account': None}
