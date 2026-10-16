import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .constants import DISPLAY_NAME_MAX_LENGTH
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Compte utilisateur. L'identifiant de connexion est l'email (toujours en minuscules)."""

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=DISPLAY_NAME_MAX_LENGTH)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    locale = models.CharField(max_length=5, default='fr')
    timezone = models.CharField(max_length=40, default='Africa/Casablanca')
    default_currency = models.CharField(max_length=3, default='MAD')
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['display_name']

    def __str__(self):
        return self.email

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None


class EmailToken(models.Model):
    """Jeton à usage unique envoyé par email. Seul son hachage est conservé."""

    class Kind(models.TextChoices):
        VERIFY_EMAIL = 'verify_email', 'Vérification de l’email'
        RESET_PASSWORD = 'reset_password', 'Réinitialisation du mot de passe'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='email_tokens'
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['user', 'kind'])]