import contextlib
import logging

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from core import error_codes
from core.exceptions import DomainError

from . import emails, selectors
from .constants import RESET_PASSWORD_TTL, VERIFY_EMAIL_TTL
from .models import EmailToken, User
from .tokens import generate_raw_token, hash_token

logger = logging.getLogger(__name__)


# --- Jetons de connexion -----------------------------------------------------


def issue_tokens(user: User) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


def revoke_all_sessions(user: User) -> None:
    """Rend inutilisables tous les jetons de rafraîchissement de l'utilisateur.

    Les jetons d'accès déjà émis restent valables jusqu'à 15 minutes (durée courte voulue).
    """
    active = OutstandingToken.objects.filter(user=user, blacklistedtoken__isnull=True)
    BlacklistedToken.objects.bulk_create(
        [BlacklistedToken(token=token) for token in active], ignore_conflicts=True
    )


def logout(*, refresh_token: str) -> None:
    """Idempotent : un jeton déjà invalide est déjà ce qu'on voulait obtenir."""
    with contextlib.suppress(TokenError):
        RefreshToken(refresh_token).blacklist()


# --- Jetons envoyés par email ------------------------------------------------


@transaction.atomic
def _create_email_token(user: User, kind: str, ttl) -> str:
    now = timezone.now()
    # un seul lien valide à la fois par type
    EmailToken.objects.filter(user=user, kind=kind, used_at__isnull=True).update(used_at=now)
    raw_token = generate_raw_token()
    EmailToken.objects.create(
        user=user, kind=kind, token_hash=hash_token(raw_token), expires_at=now + ttl
    )
    return raw_token


def _consume_email_token(raw_token: str, kind: str) -> EmailToken:
    """Retourne le jeton valide et le marque utilisé. À appeler dans une transaction."""
    token = (
        EmailToken.objects.select_for_update(of=('self',))
        .select_related('user')
        .filter(token_hash=hash_token(raw_token), kind=kind)
        .first()
    )
    now = timezone.now()
    if (
        token is None
        or token.used_at is not None
        or token.expires_at <= now
        or not token.user.is_active
    ):
        raise DomainError(
            {'token': ['Ce lien est invalide ou a expiré.']}, code=error_codes.INVALID_LINK
        )
    token.used_at = now
    token.save(update_fields=['used_at'])
    return token


def _send_safely(send, user: User, raw_token: str) -> None:
    """Un email qui échoue ne doit pas faire échouer l'action : on le journalise."""
    try:
        send(user, raw_token)
    except Exception:
        logger.exception('Envoi d’email impossible pour l’utilisateur %s', user.pk)


# --- Compte ------------------------------------------------------------------


def register_user(*, email: str, password: str, display_name: str) -> User:
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                email=email, password=password, display_name=display_name.strip()
            )
            raw_token = _create_email_token(user, EmailToken.Kind.VERIFY_EMAIL, VERIFY_EMAIL_TTL)
    except IntegrityError:
        raise DomainError(
            {'email': ['Cette adresse email est déjà utilisée.']}, code=error_codes.EMAIL_TAKEN
        ) from None
    _send_safely(emails.send_verification_email, user, raw_token)
    return user


def update_profile(*, user: User, **fields) -> User:
    """Les champs autorisés sont filtrés par le serializer, pas ici."""
    for name, value in fields.items():
        setattr(user, name, value)
    user.save(update_fields=[*fields, 'updated_at'])
    return user


@transaction.atomic
def change_password(*, user: User, old_password: str, new_password: str) -> dict[str, str]:
    if not user.check_password(old_password):
        raise DomainError(
            {'old_password': ['Mot de passe actuel incorrect.']}, code=error_codes.INVALID_PASSWORD
        )
    user.set_password(new_password)
    user.save(update_fields=['password', 'updated_at'])
    revoke_all_sessions(user)
    return issue_tokens(user)  # la session en cours continue avec de nouveaux jetons


# --- Réinitialisation du mot de passe ----------------------------------------


def request_password_reset(*, email: str) -> None:
    """Ne dit jamais si l'adresse existe : la réponse est la même dans tous les cas."""
    user = selectors.get_active_user_by_email(email)
    if user is None:
        return
    raw_token = _create_email_token(user, EmailToken.Kind.RESET_PASSWORD, RESET_PASSWORD_TTL)
    _send_safely(emails.send_password_reset_email, user, raw_token)


@transaction.atomic
def confirm_password_reset(*, raw_token: str, new_password: str) -> None:
    user = _consume_email_token(raw_token, EmailToken.Kind.RESET_PASSWORD).user
    user.set_password(new_password)
    update_fields = ['password', 'updated_at']
    if user.email_verified_at is None:  # le lien reçu par email prouve l'adresse
        user.email_verified_at = timezone.now()
        update_fields.append('email_verified_at')
    user.save(update_fields=update_fields)
    revoke_all_sessions(user)


# --- Vérification de l'email -------------------------------------------------


def request_email_verification(*, user: User) -> None:
    if user.email_verified:
        raise DomainError(
            'Votre adresse email est déjà confirmée.', code=error_codes.ALREADY_VERIFIED
        )
    raw_token = _create_email_token(user, EmailToken.Kind.VERIFY_EMAIL, VERIFY_EMAIL_TTL)
    _send_safely(emails.send_verification_email, user, raw_token)


@transaction.atomic
def confirm_email_verification(*, raw_token: str) -> User:
    user = _consume_email_token(raw_token, EmailToken.Kind.VERIFY_EMAIL).user
    if user.email_verified_at is None:
        user.email_verified_at = timezone.now()
        user.save(update_fields=['email_verified_at', 'updated_at'])
    return user