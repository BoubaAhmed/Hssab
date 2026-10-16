from .models import User


def get_active_user_by_email(email: str) -> User | None:
    return User.objects.filter(email=email.strip().lower(), is_active=True).first()


def capabilities_for(user: User) -> dict[str, bool]:
    """Ce que le frontend peut afficher ou masquer. Le serveur vérifie toujours de son côté."""
    return {'email_verified': user.email_verified, 'is_staff': user.is_staff}