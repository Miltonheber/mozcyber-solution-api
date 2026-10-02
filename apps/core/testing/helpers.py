"""Helpers de teste reutilizáveis por todas as apps."""

from apps.user.models import Permission, Profile
from apps.user.utils.tokens import build_tokens


def grant_permissions(user, codes):
    """Cria (se preciso) um perfil com as permissões `codes` e atribui-o ao utilizador."""
    codes = list(codes)
    if not codes:
        return user
    profile, _ = Profile.objects.get_or_create(code=f"test-{user.pk}", defaults={"name": "Test"})
    for code in codes:
        permission, _ = Permission.objects.get_or_create(code=code, defaults={"name": code})
        profile.permissions.add(permission)
    user.profiles.add(profile)
    return user


def bearer(user) -> str:
    """Header Authorization com JWT real (claims calculadas a partir da BD)."""
    return f"Bearer {build_tokens(user)['access']}"


def assert_error(response, status_code, code=None):
    """Valida o formato uniforme de erro {code, message, details}."""
    assert response.status_code == status_code, response.content
    assert set(response.data) == {"code", "message", "details"}
    if code:
        assert response.data["code"] == code


def assert_paginated(response, count=None, size=None):
    assert response.status_code == 200, response.content
    assert {"count", "next", "previous", "results"} <= set(response.data)
    if count is not None:
        assert response.data["count"] == count
    if size is not None:
        assert len(response.data["results"]) == size
