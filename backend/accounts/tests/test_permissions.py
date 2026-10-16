from types import SimpleNamespace

import pytest

from core.permissions import IsEmailVerified, IsStaffUser


def request_for(user):
    return SimpleNamespace(user=user)


@pytest.mark.django_db
def test_is_email_verified(make_user):
    permission = IsEmailVerified()

    assert permission.has_permission(request_for(make_user('ali', verified=True)), None) is True
    assert permission.has_permission(request_for(make_user('sara', verified=False)), None) is False


@pytest.mark.django_db
def test_is_staff_user(make_user):
    permission = IsStaffUser()

    assert permission.has_permission(request_for(make_user('ali')), None) is False
    assert permission.has_permission(request_for(make_user('root', is_staff=True)), None) is True