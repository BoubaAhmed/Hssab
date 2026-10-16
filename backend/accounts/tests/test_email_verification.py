import pytest

REQUEST = '/api/auth/email/verify/request/'
CONFIRM = '/api/auth/email/verify/confirm/'


@pytest.mark.django_db
def test_request_requires_login(api_client):
    assert api_client.post(REQUEST).status_code == 401


@pytest.mark.django_db
def test_verification_flow(api_client, make_user, client_for, mailoutbox, extract_token):
    user = make_user('ali', verified=False)

    assert client_for(user).post(REQUEST).status_code == 202
    token = extract_token(mailoutbox[0])
    r = api_client.post(CONFIRM, {'token': token}, format='json')

    assert r.status_code == 200
    assert r.json()['email_verified'] is True
    user.refresh_from_db()
    assert user.email_verified


@pytest.mark.django_db
def test_request_when_already_verified(make_user, client_for, mailoutbox):
    r = client_for(make_user('ali')).post(REQUEST)

    assert r.status_code == 400
    assert r.json()['error']['code'] == 'already_verified'
    assert mailoutbox == []


@pytest.mark.django_db
def test_unknown_token_is_refused(api_client):
    r = api_client.post(CONFIRM, {'token': 'inconnu'}, format='json')

    assert r.status_code == 400
    assert r.json()['error']['code'] == 'invalid_link'


@pytest.mark.django_db
def test_verification_link_works_only_once(
    api_client, make_user, client_for, mailoutbox, extract_token
):
    client_for(make_user('ali', verified=False)).post(REQUEST)
    token = extract_token(mailoutbox[0])

    assert api_client.post(CONFIRM, {'token': token}, format='json').status_code == 200
    assert api_client.post(CONFIRM, {'token': token}, format='json').status_code == 400