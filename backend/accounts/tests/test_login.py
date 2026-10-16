import pytest

URL = '/api/auth/login/'


@pytest.mark.django_db
def test_login_returns_tokens_and_the_user(api_client, make_user, password):
    make_user('ali')

    r = api_client.post(URL, {'email': 'ALI@example.com', 'password': password}, format='json')

    assert r.status_code == 200
    body = r.json()
    assert {'access', 'refresh', 'user'} <= set(body)
    assert body['user']['display_name'] == 'Ali'


@pytest.mark.django_db
@pytest.mark.parametrize('email', ['ali@example.com', 'inconnu@example.com'])
def test_bad_credentials_give_the_same_answer(api_client, make_user, email):
    make_user('ali')

    r = api_client.post(URL, {'email': email, 'password': 'mauvais'}, format='json')

    assert r.status_code == 401
    assert r.json()['error']['code'] == 'no_active_account'
    assert r.json()['error']['message'] == 'Email ou mot de passe incorrect.'


@pytest.mark.django_db
def test_inactive_account_cannot_log_in(api_client, make_user, password):
    make_user('ali', is_active=False)

    r = api_client.post(URL, {'email': 'ali@example.com', 'password': password}, format='json')

    assert r.status_code == 401


@pytest.mark.django_db
def test_login_is_rate_limited(api_client):
    for _ in range(10):
        api_client.post(URL, {'email': 'x@example.com', 'password': 'x'}, format='json')

    r = api_client.post(URL, {'email': 'x@example.com', 'password': 'x'}, format='json')

    assert r.status_code == 429
    assert r.json()['error']['code'] == 'throttled'