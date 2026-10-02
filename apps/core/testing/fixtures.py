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
