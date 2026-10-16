"""Format d'erreur unique : {"error": {"code": "...", "message": "...", "details": ...}}."""

from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler

from . import error_codes

# Messages français pour les erreurs que DRF produit en anglais.
FRENCH_BY_CODE = {
    error_codes.NOT_AUTHENTICATED: 'Connexion requise.',
    error_codes.NOT_FOUND: 'Élément introuvable.',
    error_codes.THROTTLED: 'Trop de tentatives. Réessayez dans un instant.',
    error_codes.TOKEN_INVALID: 'Votre session a expiré. Reconnectez-vous.',
    'method_not_allowed': 'Action non autorisée.',
    'parse_error': 'Les données envoyées sont illisibles.',
}
DRF_DEFAULT_FORBIDDEN = 'You do not have permission to perform this action.'
FORBIDDEN_MESSAGE = "Vous n'avez pas le droit de faire cela."
VALIDATION_MESSAGE = 'Les données envoyées sont invalides.'


class DomainError(APIException):
    """Une règle de gestion est violée. Répond 400, avec un code d'erreur au choix."""

    status_code = 400
    default_code = error_codes.DOMAIN_ERROR
    default_detail = 'Opération impossible.'

    def __init__(self, detail=None, code=None):
        super().__init__(detail, code)
        self.error_code = code or self.default_code


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None  # erreur serveur : laissée à Django

    data = response.data
    code = getattr(exc, 'error_code', None) or getattr(exc, 'default_code', 'error')

    if isinstance(data, dict) and 'detail' in data:
        detail = data['detail']
        code = getattr(detail, 'code', None) or code
        message = str(detail)
        details = None
        if code in FRENCH_BY_CODE:
            message = FRENCH_BY_CODE[code]
        elif message == DRF_DEFAULT_FORBIDDEN:
            message = FORBIDDEN_MESSAGE
    else:
        message = VALIDATION_MESSAGE
        details = data

    response.data = {'error': {'code': str(code), 'message': message, 'details': details}}
    return response