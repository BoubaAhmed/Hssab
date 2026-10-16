from datetime import timedelta

VERIFY_EMAIL_TTL = timedelta(hours=48)
RESET_PASSWORD_TTL = timedelta(hours=1)
DISPLAY_NAME_MAX_LENGTH = 60
SUPPORTED_LOCALES = ('fr', 'ar', 'en')