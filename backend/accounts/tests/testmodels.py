import pytest

from accounts.models import User


@pytest.mark.django_db
def test_create_user_normalizes_the_email():
    user = User.objects.create_user(email='  Ali@EXAMPLE.com ', password='x', display_name='Ali')

    assert user.email == 'ali@example.com'
    assert not user.email_verified
    assert user.public_id is not None


@pytest.mark.django_db
def test_email_is_required():
    with pytest.raises(ValueError):
        User.objects.create_user(email='', password='x')


@pytest.mark.django_db
def test_display_name_defaults_to_the_email_prefix():
    user = User.objects.create_user(email='karim@example.com', password='x')

    assert user.display_name == 'karim'


@pytest.mark.django_db
def test_superuser_is_verified_and_staff():
    user = User.objects.create_superuser(email='root@example.com', password='x')

    assert user.is_staff and user.is_superuser and user.email_verified