from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import BaseUserCreationForm
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm

from apps.core.admin import AuditedAdmin
from apps.user.models import Permission, Profile, User


class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ("email", "name", "profiles")


class UserChangeForm(DjangoUserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(AuditedAdmin, DjangoUserAdmin):
    """Login por email; a palavra-passe é sempre guardada com hash (formulário de criação do Django)."""

    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ("email", "name", "is_active", "is_staff", "last_login")
    list_filter = ("is_active", "is_staff", "is_superuser", "profiles")
    search_fields = ("email", "name")
    ordering = ("email",)
    filter_horizontal = ("profiles", "groups", "user_permissions")
    readonly_fields = ("last_login",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Dados", {"fields": ("name", "profiles")}),
        ("Estado", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Datas", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "name", "password1", "password2", "profiles")}),
    )


@admin.register(Profile)
class ProfileAdmin(AuditedAdmin):
    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    filter_horizontal = ("permissions",)


@admin.register(Permission)
class PermissionAdmin(AuditedAdmin):
    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
