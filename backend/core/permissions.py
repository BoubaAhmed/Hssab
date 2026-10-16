from rest_framework.permissions import BasePermission

from . import error_codes


class IsEmailVerified(BasePermission):
    """Réserve une action aux comptes dont l'adresse email est confirmée."""

    message = 'Confirmez votre adresse email pour effectuer cette action.'
    code = error_codes.EMAIL_NOT_VERIFIED

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.email_verified_at)


class IsStaffUser(BasePermission):
    """Réservé à l'équipe Hssab (jamais utilisé par les utilisateurs normaux)."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff)