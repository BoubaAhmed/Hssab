import pytest

URL = '/api/auth/me/'


@pytest.mark.django_db
def test_me_requires_authentication(api_client):
    r = api_client.get(URL)

    assert r.status_code == 401
    assert r.json()['error']['code'] == 'not_authenticated'


@pytest.mark.django_db
def test_me_returns_the_profile_and_capabilities(make_user, client_for):
    user = make_user('ali')

    body = client_for(user).get(URL).json()

    assert body['email'] == 'ali@example.com'
    assert body['id'] == str(user.public_id)
    assert body['capabilities'] == {'email_verified': True, 'is_staff': False}
    assert 'password' not in body


@pytest.mark.django_db
def test_patch_updates_the_profile(make_user, client_for):
    user = make_user('ali')

    r = client_for(user).patch(
        URL, {'display_name': 'Ali B.', 'locale': 'ar', 'default_currency': 'EUR'}, format='json'
    )

    assert r.status_code == 200
    user.refresh_from_db()
    assert (user.display_name, user.locale, user.default_currency) == ('Ali B.', 'ar', 'EUR')


@pytest.mark.django_db
@pytest.mark.parametrize(
    'changes',
    [{'timezone': 'Mars/Olympus'}, {'locale': 'xx'}, {'default_currency': 'mad'}, {'display_name': ''}],
)
def test_patch_validates_the_input(make_user, client_for, changes):
    r = client_for(make_user('ali')).patch(URL, changes, format='json')

    assert r.status_code == 400


@pytest.mark.django_db
def test_patch_cannot_change_email_or_rights(make_user, client_for):
    user = make_user('ali')

    client_for(user).patch(URL, {'email': 'autre@example.com', 'is_staff': True}, format='json')

    user.refresh_from_db()
    assert user.email == 'ali@example.com'
    assert user.is_staff is False