from datetime import timedelta

import pytest
from django.utils import timezone

from accounts.models import EmailToken

LOGIN = '/api/auth/login/'
REFRESH = '/api/auth/refresh/'
CHANGE = '/api/auth/password/change/'
RESET_REQUEST = '/api/auth/password/reset/request/'
RESET_CONFIRM = '/api/auth/password/reset/confirm/'
NEW = 'N0uveau-mot-de-passe!'


def log_in(api_client, password):
    r = api_client.post(LOGIN, {'email': 'ali@example.com', 'password': password}, format='json')
    return r.json()


# --- Changer son mot de passe --------------------------------------------------


@pytest.mark.django_db
def test_change_password_revokes_old_sessions(api_client, make_user, client_for, password):
    user = make_user('ali')
    old = log_in(api_client, password)

    r = client_for(user).post(CHANGE, {'old_password': password, 'new_password': NEW}, format='json')

    assert r.status_code == 200
    assert {'access', 'refresh'} <= set(r.json())
    assert api_client.post(REFRESH, {'refresh': old['refresh']}, format='json').status_code == 401
    assert log_in(api_client, NEW)['user']['email'] == 'ali@example.com'


@pytest.mark.django_db
def test_change_password_needs_the_current_one(make_user, client_for):
    r = client_for(make_user('ali')).post(
        CHANGE, {'old_password': 'faux', 'new_password': NEW}, format='json'
    )

    assert r.status_code == 400
    assert r.json()['error']['code'] == 'invalid_password'


@pytest.mark.django_db
def test_change_password_refuses_a_weak_or_identical_password(make_user, client_for, password):
    client = client_for(make_user('ali'))

    weak = client.post(CHANGE, {'old_password': password, 'new_password': '123'}, format='json')
    same = client.post(CHANGE, {'old_password': password, 'new_password': password}, format='json')

    assert weak.status_code == 400
    assert same.status_code == 400


@pytest.mark.django_db
def test_change_password_requires_login(api_client):
    r = api_client.post(CHANGE, {'old_password': 'a', 'new_password': 'b'}, format='json')

    assert r.status_code == 401


# --- Mot de passe oublié -------------------------------------------------------


@pytest.mark.django_db
def test_reset_request_never_reveals_whether_an_email_exists(api_client, make_user, mailoutbox):
    make_user('ali')

    known = api_client.post(RESET_REQUEST, {'email': 'ali@example.com'}, format='json')
    unknown = api_client.post(RESET_REQUEST, {'email': 'inconnu@example.com'}, format='json')

    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert len(mailoutbox) == 1  # seul le compte existant reçoit un email


@pytest.mark.django_db
def test_reset_flow(api_client, make_user, mailoutbox, extract_token, password):
    user = make_user('ali', verified=False)
    old = log_in(api_client, password)
    api_client.post(RESET_REQUEST, {'email': 'ali@example.com'}, format='json')
    token = extract_token(mailoutbox[0])

    r = api_client.post(RESET_CONFIRM, {'token': token, 'new_password': NEW}, format='json')

    assert r.status_code == 200
    user.refresh_from_db()
    assert user.check_password(NEW)
    assert user.email_verified  # le lien reçu par email prouve l'adresse
    assert api_client.post(REFRESH, {'refresh': old['refresh']}, format='json').status_code == 401


@pytest.mark.django_db
def test_reset_link_works_only_once(api_client, make_user, mailoutbox, extract_token):
    make_user('ali')
    api_client.post(RESET_REQUEST, {'email': 'ali@example.com'}, format='json')
    token = extract_token(mailoutbox[0])
    payload = {'token': token, 'new_password': NEW}

    assert api_client.post(RESET_CONFIRM, payload, format='json').status_code == 200
    again = api_client.post(RESET_CONFIRM, payload, format='json')

    assert again.status_code == 400
    assert again.json()['error']['code'] == 'invalid_link'


@pytest.mark.django_db
def test_reset_link_expires(api_client, make_user, mailoutbox, extract_token):
    make_user('ali')
    api_client.post(RESET_REQUEST, {'email': 'ali@example.com'}, format='json')
    token = extract_token(mailoutbox[0])
    EmailToken.objects.update(expires_at=timezone.now() - timedelta(minutes=1))

    r = api_client.post(RESET_CONFIRM, {'token': token, 'new_password': NEW}, format='json')

    assert r.status_code == 400
    assert r.json()['error']['code'] == 'invalid_link'


@pytest.mark.django_db
def test_weak_new_password_does_not_burn_the_link(api_client, make_user, mailoutbox, extract_token):
    make_user('ali')
    api_client.post(RESET_REQUEST, {'email': 'ali@example.com'}, format='json')
    token = extract_token(mailoutbox[0])

    weak = api_client.post(RESET_CONFIRM, {'token': token, 'new_password': '123'}, format='json')
    good = api_client.post(RESET_CONFIRM, {'token': token, 'new_password': NEW}, format='json')

    assert weak.status_code == 400
    assert good.status_code == 200


@pytest.mark.django_db
def test_a_new_reset_request_invalidates_the_previous_link(
    api_client, make_user, mailoutbox, extract_token
):
    make_user('ali')
    api_client.post(RESET_REQUEST, {'email': 'ali@example.com'}, format='json')
    api_client.post(RESET_REQUEST, {'email': 'ali@example.com'}, format='json')
    first, second = (extract_token(message) for message in mailoutbox)

    old = api_client.post(RESET_CONFIRM, {'token': first, 'new_password': NEW}, format='json')
    new = api_client.post(RESET_CONFIRM, {'token': second, 'new_password': NEW}, format='json')

    assert old.status_code == 400
    assert new.status_code == 200