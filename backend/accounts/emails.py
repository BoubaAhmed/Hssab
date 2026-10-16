from django.conf import settings
from django.core.mail import send_mail

from .constants import RESET_PASSWORD_TTL, VERIFY_EMAIL_TTL


def _link(path: str, raw_token: str) -> str:
    base = settings.FRONTEND_URL.rstrip('/')
    return f'{base}{path}?token={raw_token}'


def send_verification_email(user, raw_token: str) -> None:
    link = _link('/verify-email', raw_token)
    hours = int(VERIFY_EMAIL_TTL.total_seconds() // 3600)
    send_mail(
        subject='Confirmez votre adresse email – Hssab',
        message=(
            f'Bonjour {user.display_name},\n\n'
            f'Confirmez votre adresse email en ouvrant ce lien :\n{link}\n\n'
            f'Ce lien est valable {hours} heures.\n'
            'Si vous n’êtes pas à l’origine de cette demande, ignorez ce message.'
        ),
        from_email=None,
        recipient_list=[user.email],
    )


def send_password_reset_email(user, raw_token: str) -> None:
    link = _link('/reset-password', raw_token)
    minutes = int(RESET_PASSWORD_TTL.total_seconds() // 60)
    send_mail(
        subject='Réinitialisation de votre mot de passe – Hssab',
        message=(
            f'Bonjour {user.display_name},\n\n'
            f'Choisissez un nouveau mot de passe en ouvrant ce lien :\n{link}\n\n'
            f'Ce lien est valable {minutes} minutes et ne peut servir qu’une fois.\n'
            'Si vous n’avez rien demandé, ignorez ce message : votre mot de passe reste inchangé.'
        ),
        from_email=None,
        recipient_list=[user.email],
    )