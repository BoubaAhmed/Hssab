import pytest

LOGIN = '/api/auth/login/'
REFRESH = '/api/auth/refresh/'
LOGOUT = '/api/auth/logout/'
ME = '/api/auth/me/'


def log_in(api_client, password):
    r = api_client.post(LOGIN, {'email': 'ali@example.com', 'password': password}, format='json')
    return r.json()


@pytest.mark.django_db
def test_refresh_rotates_the_token_and_revokes_the_old_one(api_client, make_user, password):
    make_user('ali')
    tokens = log_in(api_client, password)

    r = api_client.post(REFRESH, {'refresh': tokens['refresh']}, format='json')

    assert r.status_code == 200
    assert r.json()['refresh'] != tokens['refresh']
    again = api_client.post(REFRESH, {'refresh': tokens['refresh']}, format='json')
    assert again.status_code == 401
    assert again.json()['error']['code'] == 'token_not_valid'


@pytest.mark.django_db
def test_logout_revokes_the_refresh_token(api_client, make_user, password):
    make_user('ali')
    tokens = log_in(api_client, password)

    r = api_client.post(LOGOUT, {'refresh': tokens['refresh']}, format='json')

    assert r.status_code == 204
    assert api_client.post(REFRESH, {'refresh': tokens['refresh']}, format='json').status_code == 401


@pytest.mark.django_db
def test_logout_with_an_invalid_token_is_still_fine(api_client):
    r = api_client.post(LOGOUT, {'refresh': 'n-importe-quoi'}, format='json')

    assert r.status_code == 204


@pytest.mark.django_db
def test_access_token_opens_protected_routes(api_client, make_user, password):
    make_user('ali')
    tokens = log_in(api_client, password)

    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')

    assert api_client.get(ME).status_code == 200


@pytest.mark.django_db
def test_invalid_access_token_is_refused(api_client):
    api_client.credentials(HTTP_AUTHORIZATION='Bearer invalide')

    r = api_client.get(ME)

    assert r.status_code == 401
    assert r.json()['error']['code'] == 'token_not_valid'


@pytest.mark.django_db
def test_an_old_token_does_not_block_public_routes(api_client, make_user, password):
    make_user('ali')
    api_client.credentials(HTTP_AUTHORIZATION='Bearer invalide')

    r = api_client.post(LOGIN, {'email': 'ali@example.com', 'password': password}, format='json')

    assert r.status_code == 200