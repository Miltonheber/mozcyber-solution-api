import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_any_origin_is_allowed(api_client):
    response = api_client.options(
        reverse("auth-login", kwargs={"version": "v1"}),
        HTTP_ORIGIN="https://qualquer-site.com",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
    )
    assert response["Access-Control-Allow-Origin"] == "*"
