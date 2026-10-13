import pytest

from expenses.models import Group


@pytest.mark.django_db
def test_chaque_groupe_a_un_code_unique():
    a = Group.objects.create(name='Coloc')
    b = Group.objects.create(name='Voyage')
    assert a.invite_code != b.invite_code