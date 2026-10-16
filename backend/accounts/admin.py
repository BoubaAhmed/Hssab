from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import BaseUserCreationForm
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm

from .models import EmailToken, User


class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'display_name')


class UserChangeForm(BaseUserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    ordering = ('email',)
    list_display = ('email', 'display_name', 'is_active', 'email_verified_at', 'is_staff', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'display_name')
    readonly_fields = ('public_id', 'last_login', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Profil', {'fields': ('display_name', 'locale', 'timezone', 'default_currency')}),
        ('État du compte', {'fields': ('is_active', 'email_verified_at', 'deleted_at')}),
        ('Droits', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('public_id', 'last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'display_name', 'password1', 'password2')}),
    )


@admin.register(EmailToken)
class EmailTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'kind', 'expires_at', 'used_at', 'created_at')
    list_filter = ('kind',)
    readonly_fields = [field.name for field in EmailToken._meta.fields]

    def has_add_permission(self, request):
        return False