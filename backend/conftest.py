import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

PASSWORD = 'Str0ng-pass-123'


@pytest.fixture(autouse=True)
def _reset_throttling():
    """Les limites de requêtes sont en cache : on repart de zéro à chaque test."""
    cache.clear()


@pytest.fixture
def password():
    return PASSWORD


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_user(db):
    """make_user('ali') crée ali@example.com, email confirmé, mot de passe PASSWORD."""

    def _make_user(name='ali', *, verified=True, **extra):
        user = get_user_model().objects.create_user(
            email=f'{name}@example.com',
            password=PASSWORD,
            display_name=name.capitalize(),
            **extra,
        )
        if verified:
            user.email_verified_at = timezone.now()
            user.save(update_fields=['email_verified_at'])
        return user

    return _make_user


@pytest.fixture
def client_for():
    """client_for(user) renvoie un client d'API connecté en tant que cet utilisateur."""

    def _client_for(user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return _client_for