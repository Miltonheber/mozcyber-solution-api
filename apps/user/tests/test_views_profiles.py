import pytest
from django.urls import reverse

from apps.core.testing.helpers import assert_error, assert_paginated
from apps.user.tests.factories import PermissionFactory, ProfileFactory

pytestmark = pytest.mark.django_db


def list_url(name="profile-list"):
    return reverse(name, kwargs={"version": "v1"})


def test_profile_crud_with_permissions(auth_client):
    PermissionFactory(code="x:read")
    client = auth_client(["profile:create", "profile:read", "profile:update", "profile:delete"])
    created = client.post(
        list_url(), {"code": "ops", "name": "Ops", "permissions": ["x:read"]}, format="json"
    )
    assert created.status_code == 201 and created.data["permissions"] == ["x:read"]
    detail = reverse("profile-detail", kwargs={"version": "v1", "pk": created.data["id"]})
    assert client.get(detail).data["code"] == "ops"
    assert client.patch(detail, {"permissions": []}, format="json").data["permissions"] == []
    assert client.delete(detail).status_code == 204


def test_profile_list_no_n_plus_1(auth_client, django_assert_max_num_queries):
    perms = PermissionFactory.create_batch(3)
    for _ in range(8):
        ProfileFactory().permissions.set(perms)
    client = auth_client(["profile:read"])
    with django_assert_max_num_queries(6):
        assert_paginated(client.get(list_url()), count=8 + 1)  # +1 perfil de teste do utilizador


def test_profile_forbidden_and_unknown_permission(auth_client):
    assert_error(auth_client([]).get(list_url()), 403)
    response = auth_client(["profile:create"]).post(
        list_url(), {"code": "z", "name": "Z", "permissions": ["nope"]}, format="json"
    )
    assert_error(response, 400, "validation_error")


def test_permission_endpoints(auth_client):
    client = auth_client(["permission:create", "permission:read"])
    created = client.post(list_url("permission-list"), {"code": "new:perm", "name": "New"}, format="json")
    assert created.status_code == 201
    assert_paginated(client.get(list_url("permission-list"), {"search": "new:"}), count=1)
