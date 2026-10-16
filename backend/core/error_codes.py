"""Codes d'erreur stables de l'API : le frontend traduit chaque code en message."""

# Authentification
INVALID_CREDENTIALS = 'no_active_account'
TOKEN_INVALID = 'token_not_valid'
EMAIL_TAKEN = 'email_taken'
INVALID_PASSWORD = 'invalid_password'
INVALID_LINK = 'invalid_link'
ALREADY_VERIFIED = 'already_verified'
EMAIL_NOT_VERIFIED = 'email_not_verified'

# Génériques
VALIDATION_ERROR = 'invalid'
NOT_AUTHENTICATED = 'not_authenticated'
PERMISSION_DENIED = 'permission_denied'
NOT_FOUND = 'not_found'
THROTTLED = 'throttled'
DOMAIN_ERROR = 'domain_error'