import pytest

URL = '/api/auth/register/'
PAYLOAD = {'email': 'Sara@Example.com', 'password': 'Str0ng-pass-123', 'display_name': 'Sara'}


@pytest.mark.django_db
def test_register_returns_the_user_and_tokens(api_client):
    r = api_client.post(URL, PAYLOAD, format='json')

    assert r.status_code == 201
    body = r.json()
    assert body['user']['email'] == 'sara@example.com'
    assert body['user']['email_verified'] is False
    assert {'access', 'refresh'} <= set(body)
    assert 'password' not in body['user']


@pytest.mark.django_db
def test_register_sends_a_verification_email(api_client, mailoutbox, extract_token):
    api_client.post(URL, PAYLOAD, format='json')

    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ['sara@example.com']
    assert extract_token(mailoutbox[0])


@pytest.mark.django_db
def test_register_refuses_a_duplicate_email_whatever_the_case(api_client, make_user):
    make_user('sara')

    r = api_client.post(URL, PAYLOAD, format='json')

    assert r.status_code == 400
    assert 'email' in r.json()['error']['details']


@pytest.mark.django_db
@pytest.mark.parametrize(
    'changes',
    [{'password': '123'}, {'password': 'password'}, {'email': 'pas-un-email'}, {'display_name': ''}],
)
def test_register_validates_the_input(api_client, changes):
    r = api_client.post(URL, {**PAYLOAD, **changes}, format='json')

    assert r.status_code == 400
    assert r.json()['error']['code'] == 'invalid'


@pytest.mark.django_db
def test_register_is_rate_limited(api_client):
    for index in range(10):
        api_client.post(URL, {**PAYLOAD, 'email': f'u{index}@example.com'}, format='json')

    r = api_client.post(URL, {**PAYLOAD, 'email': 'extra@example.com'}, format='json')

    assert r.status_code == 429
    assert r.json()['error']['code'] == 'throttled'