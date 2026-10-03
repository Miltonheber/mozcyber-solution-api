import pytest
from rest_framework.test import APIClient

from apps.user.tests.factories import UserFactory

from .helpers import bearer, grant_permissions


@pytest.fixture(autouse=True)
def fast_password_hasher(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(db):
    """Fábrica: auth_client(["user:read"]) -> APIClient autenticado com JWT real e essas permissões.
    O utilizador fica em `client.user`."""

    def make(permissions=(), user=None):
        user = user or UserFactory()
        grant_permissions(user, permissions)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=bearer(user))
        client.user = user
        return client

    return make


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    """Os contadores de throttling vivem na cache; limpar entre testes."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def staff_client(db, settings):
    """Django `Client` com sessão de um superutilizador (para o admin). O utilizador fica em `client.user`.
    Usa o storage de estáticos simples: o do WhiteNoise (manifesto) exige `collectstatic`."""
    from django.test import Client

    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }

    staff = UserFactory(is_staff=True, is_superuser=True)
    client = Client()
    client.force_login(staff)
    client.user = staff
    return client
