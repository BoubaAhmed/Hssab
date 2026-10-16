from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from core import error_codes

from . import selectors
from .constants import DISPLAY_NAME_MAX_LENGTH, SUPPORTED_LOCALES
from .models import User


def check_password_strength(password: str, user: User | None = None) -> str:
    """Applique les règles de mot de passe de Django et renvoie des erreurs lisibles."""
    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(list(exc.messages)) from exc
    return password


class UserSerializer(serializers.ModelSerializer):
    """Ce que le frontend reçoit d'un utilisateur (jamais d'identifiant interne ni de mot de passe)."""

    id = serializers.UUIDField(source='public_id', read_only=True)
    email_verified = serializers.BooleanField(read_only=True)
    capabilities = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'display_name',
            'email_verified',
            'locale',
            'timezone',
            'default_currency',
            'capabilities',
            'created_at',
        ]
        read_only_fields = fields

    def get_capabilities(self, user):
        return selectors.capabilities_for(user)


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    display_name = serializers.CharField(max_length=DISPLAY_NAME_MAX_LENGTH)

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                'Cette adresse email est déjà utilisée.', code=error_codes.EMAIL_TAKEN
            )
        return email

    def validate(self, attrs):
        candidate = User(email=attrs['email'], display_name=attrs['display_name'])
        try:
            validate_password(attrs['password'], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)}) from exc
        return attrs


class LoginSerializer(TokenObtainPairSerializer):
    default_error_messages = {'no_active_account': 'Email ou mot de passe incorrect.'}

    def validate(self, attrs):
        attrs[self.username_field] = str(attrs[self.username_field]).strip().lower()
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ProfileUpdateSerializer(serializers.Serializer):
    display_name = serializers.CharField(max_length=DISPLAY_NAME_MAX_LENGTH, required=False)
    locale = serializers.ChoiceField(choices=SUPPORTED_LOCALES, required=False)
    timezone = serializers.CharField(max_length=40, required=False)
    default_currency = serializers.RegexField(
        r'^[A-Z]{3}$',
        required=False,
        error_messages={'invalid': 'Code devise invalide (par exemple MAD).'},
    )

    def validate_timezone(self, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise serializers.ValidationError('Fuseau horaire inconnu.') from None
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError(
                {'new_password': ['Le nouveau mot de passe doit être différent de l’ancien.']}
            )
        try:
            validate_password(attrs['new_password'], user=self.context['request'].user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'new_password': list(exc.messages)}) from exc
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_new_password(self, value):
        return check_password_strength(value)


class ConfirmTokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)