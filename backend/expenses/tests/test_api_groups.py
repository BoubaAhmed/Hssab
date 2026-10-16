import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from expenses.models import Group, Member

User = get_user_model()
PASSWORD = 'Str0ng-pass-123'

@pytest.fixture
def ali(make_user):
    return make_user('ali')


@pytest.fixture
def sara(make_user):
    return make_user('sara')


@pytest.fixture
def api():
    return APIClient()


def test_groups_require_login(api, db):
    assert api.get('/api/groups/').status_code == 401


def test_creating_a_group_makes_me_a_member(api, ali):
    api.force_authenticate(user=ali)
    r = api.post('/api/groups/', {'name': 'Coloc', 'currency': 'MAD'}, format='json')
    assert r.status_code == 201
    assert [m['display_name'] for m in r.json()['members']] == ['ali']


def test_i_only_see_my_groups(api, ali, sara):
    mine = Group.objects.create(name='Mine')
    Member.objects.create(group=mine, user=ali, display_name='ali')
    other = Group.objects.create(name='Other')
    Member.objects.create(group=other, user=sara, display_name='sara')

    api.force_authenticate(user=ali)
    names = [g['name'] for g in api.get('/api/groups/').json()]
    assert names == ['Mine']


def test_a_stranger_cannot_read_a_group(api, ali, sara):
    group = Group.objects.create(name='Private')
    Member.objects.create(group=group, user=ali, display_name='ali')

    api.force_authenticate(user=sara)
    assert api.get(f'/api/groups/{group.id}/').status_code == 404


def test_join_with_invite_code(api, ali, sara):
    group = Group.objects.create(name='Trip')
    Member.objects.create(group=group, user=ali, display_name='ali')

    api.force_authenticate(user=sara)
    r = api.post(f'/api/join/{group.invite_code}/', {'display_name': 'Sara'}, format='json')
    assert r.status_code == 201
    assert group.members.filter(user=sara).exists()

    # joining twice does not create a duplicate
    r = api.post(f'/api/join/{group.invite_code}/', format='json')
    assert r.status_code == 200
    assert group.members.filter(user=sara).count() == 1


def test_wrong_invite_code(api, ali):
    api.force_authenticate(user=ali)
    assert api.post('/api/join/does-not-exist/').status_code == 404