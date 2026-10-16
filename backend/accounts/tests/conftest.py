import re

import pytest


@pytest.fixture
def extract_token():
    """Lit le jeton dans le lien d'un email envoyé par l'application."""

    def _extract(message):
        return re.search(r'token=([\w-]+)', message.body).group(1)

    return _extract