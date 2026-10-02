import pytest
from django.urls import reverse

from apps.core.testing.helpers import assert_error

pytestmark = pytest.mark.django_db


def test_business_exception_uniform_format(api_client):
    response = api_client.post(
        reverse("auth-login", kwargs={"version": "v1"}), {"email": "x@y.com", "password": "bad"}
    )
    assert_error(response, 401, "invalid_credentials")


def test_validation_error_uniform_format(api_client):
    response = api_client.post(reverse("auth-login", kwargs={"version": "v1"}), {})
    assert_error(response, 400, "validation_error")
    assert "email" in response.data["details"]


def test_unauthenticated_is_401(api_client):
    assert_error(api_client.get(reverse("user-list", kwargs={"version": "v1"})), 401, "unauthorized")


def test_unknown_version_is_404(api_client):
    assert api_client.get("/api/v9/users/").status_code == 404
