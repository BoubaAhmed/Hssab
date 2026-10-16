from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Une adresse email est obligatoire.')
        email = email.strip().lower()
        extra_fields.setdefault('display_name', email.split('@')[0])
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('email_verified_at', timezone.now())
        if not (extra_fields['is_staff'] and extra_fields['is_superuser']):
            raise ValueError('Un super-utilisateur doit avoir is_staff et is_superuser à True.')
        return self.create_user(email, password, **extra_fields)