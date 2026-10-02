import pytest
from django.urls import reverse

from apps.core.testing.helpers import assert_error
from apps.user.tests.factories import DEFAULT_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db


def url(name):
    return reverse(name, kwargs={"version": "v1"})


def test_login_by_email(api_client):
    user = UserFactory(email="login@example.com")
    response = api_client.post(url("auth-login"), {"email": user.email, "password": DEFAULT_PASSWORD})
    assert response.status_code == 200
    assert set(response.data) == {"access", "refresh"}


def test_login_invalid_credentials(api_client):
    response = api_client.post(url("auth-login"), {"email": "no@example.com", "password": "x"})
    assert_error(response, 401, "invalid_credentials")


def test_refresh_ok_and_invalid(api_client):
    user = UserFactory()
    tokens = api_client.post(url("auth-login"), {"email": user.email, "password": DEFAULT_PASSWORD}).data
    ok = api_client.post(url("auth-refresh"), {"refresh": tokens["refresh"]})
    assert ok.status_code == 200 and "access" in ok.data
    assert_error(api_client.post(url("auth-refresh"), {"refresh": "bad"}), 401, "invalid_token")


def test_me_requires_auth_and_returns_claims(api_client, auth_client):
    assert_error(api_client.get(url("auth-me")), 401)
    client = auth_client(["user:read"])
    response = client.get(url("auth-me"))
    assert response.status_code == 200
    assert response.data["email"] == client.user.email
    assert response.data["claims"]["permissions"] == ["user:read"]
