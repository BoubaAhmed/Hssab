import secrets

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


def generate_invite_code():
    return secrets.token_urlsafe(8)


class Group(models.Model):
    name = models.CharField(max_length=100)
    currency = models.CharField(max_length=3, default='MAD')
    invite_code = models.CharField(
        max_length=32, unique=True, default=generate_invite_code
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Member(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    display_name = models.CharField(max_length=60)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['group', 'user'],
                condition=models.Q(user__isnull=False),
                name='unique_user_per_group',
            )
        ]

    def __str__(self):
        return self.display_name


class Expense(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='expenses')
    payer = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='paid')
    amount_cents = models.BigIntegerField(validators=[MinValueValidator(1)])
    description = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.description} ({self.amount_cents} centimes)'


class ExpenseShare(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='shares')
    member = models.ForeignKey(Member, on_delete=models.PROTECT)
    amount_cents = models.BigIntegerField(validators=[MinValueValidator(0)])


class Settlement(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='settlements')
    from_member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='+')
    to_member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='+')
    amount_cents = models.BigIntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)