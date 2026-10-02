from unittest.mock import MagicMock

import pytest

from apps.core.exceptions import UnauthorizedException
from apps.user.services import AuthService, UserService
from apps.user.tests.factories import DEFAULT_PASSWORD, UserFactory


def test_user_service_hashes_password_without_db():
    repo = MagicMock()
    UserService(repository=repo).create({"email": "a@b.com", "password": "Secret123!"})
    kwargs = repo.create.call_args.kwargs
    assert kwargs["password"] != "Secret123!" and "$" in kwargs["password"]


@pytest.mark.django_db
def test_login_success_returns_tokens():
    user = UserFactory()
    tokens = AuthService().login(user.email, DEFAULT_PASSWORD)
    assert set(tokens) == {"access", "refresh"}
    user.refresh_from_db()
    assert user.last_login is not None


@pytest.mark.django_db
def test_login_wrong_password_and_inactive():
    user = UserFactory()
    with pytest.raises(UnauthorizedException):
        AuthService().login(user.email, "wrong")
    inactive = UserFactory(is_active=False)
    with pytest.raises(UnauthorizedException):
        AuthService().login(inactive.email, DEFAULT_PASSWORD)


@pytest.mark.django_db
def test_refresh_recomputes_claims():
    from rest_framework_simplejwt.tokens import AccessToken

    from apps.core.testing.helpers import grant_permissions

    user = UserFactory()
    refresh = AuthService().login(user.email, DEFAULT_PASSWORD)["refresh"]
    grant_permissions(user, ["user:read"])  # permissões mudam depois do login
    access = AuthService().refresh(refresh)["access"]
    assert AccessToken(access)["permissions"] == ["user:read"]


@pytest.mark.django_db
def test_refresh_invalid_token():
    with pytest.raises(UnauthorizedException):
        AuthService().refresh("garbage")
