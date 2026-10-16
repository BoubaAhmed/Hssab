import hashlib
import secrets


def generate_raw_token() -> str:
    """Jeton aléatoire envoyé par email. Il n'est jamais stocké en clair."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()