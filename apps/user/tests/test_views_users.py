import pytest
from django.urls import reverse

from apps.core.testing.helpers import assert_error, assert_paginated
from apps.user.models import User
from apps.user.tests.factories import ProfileFactory, UserFactory

pytestmark = pytest.mark.django_db


def list_url():
    return reverse("user-list", kwargs={"version": "v1"})


def detail_url(pk):
    return reverse("user-detail", kwargs={"version": "v1", "pk": pk})


def test_list_requires_permission(auth_client):
    assert_error(auth_client([]).get(list_url()), 403, "permission_denied")


def test_list_paginated_with_page_and_size(auth_client):
    UserFactory.create_batch(5)
    client = auth_client(["user:read"])  # + 1 utilizador autenticado = 6
    assert_paginated(client.get(list_url(), {"size": 2}), count=6, size=2)
    assert_paginated(client.get(list_url(), {"size": 2, "page": 3}), count=6, size=2)
    assert client.get(list_url(), {"size": 2, "page": 99}).status_code == 404


def test_list_has_constant_queries_no_n_plus_1(auth_client, django_assert_max_num_queries):
    profiles = ProfileFactory.create_batch(3)
    for _ in range(10):
        UserFactory().profiles.set(profiles)
    client = auth_client(["user:read"])
    with django_assert_max_num_queries(6):  # auth, count, users, profiles prefetch (+ margem)
        response = client.get(list_url(), {"size": 20})
    assert response.status_code == 200 and len(response.data["results"][0]["profiles"]) in (0, 3)


def test_search_filter(auth_client):
    UserFactory(email="findme@example.com")
    response = auth_client(["user:read"]).get(list_url(), {"search": "findme"})
    assert_paginated(response, count=1)


def test_create_user_with_profile(auth_client):
    profile = ProfileFactory(code="support")
    client = auth_client(["user:create"])
    response = client.post(
        list_url(),
        {"email": "new@example.com", "password": "Str0ng!Pass99", "profiles": ["support"]},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["profiles"][0]["id"] == str(profile.id)
    created = User.objects.get(email="new@example.com")
    assert created.check_password("Str0ng!Pass99") and created.created_by == client.user
    assert "password" not in response.data


def test_create_validation_and_forbidden(auth_client):
    assert_error(
        auth_client(["user:create"]).post(list_url(), {"email": "bad"}, format="json"),
        400,
        "validation_error",
    )
    assert_error(auth_client(["user:read"]).post(list_url(), {}, format="json"), 403)


def test_create_duplicate_email(auth_client):
    UserFactory(email="dup@example.com")
    response = auth_client(["user:create"]).post(
        list_url(), {"email": "dup@example.com", "password": "Str0ng!Pass99"}, format="json"
    )
    assert_error(response, 400, "validation_error")


def test_retrieve_ok_and_404(auth_client):
    target = UserFactory()
    client = auth_client(["user:read"])
    assert client.get(detail_url(target.pk)).data["email"] == target.email
    assert_error(client.get(detail_url("00000000-0000-0000-0000-000000000000")), 404, "not_found")


def test_patch_user_keeps_own_email_and_changes_password(auth_client):
    target = UserFactory(email="keep@example.com")
    client = auth_client(["user:update"])
    response = client.patch(
        detail_url(target.pk),
        {"email": "keep@example.com", "name": "New", "password": "An0ther!Pass77"},
        format="json",
    )
    assert response.status_code == 200 and response.data["name"] == "New"
    target.refresh_from_db()
    assert target.check_password("An0ther!Pass77") and target.updated_by == client.user


def test_delete_user(auth_client):
    target = UserFactory()
    client = auth_client(["user:delete"])
    assert client.delete(detail_url(target.pk)).status_code == 204
    assert not User.objects.filter(pk=target.pk).exists()
    assert_error(auth_client([]).delete(detail_url(target.pk)), 403)
