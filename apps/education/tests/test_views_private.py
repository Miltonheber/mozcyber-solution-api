import pytest
from django.urls import reverse

from apps.core.testing.helpers import assert_error, assert_paginated
from apps.education.constants import PostStatus
from apps.education.models import Post
from apps.education.tests.factories import PostFactory

pytestmark = pytest.mark.django_db

ALL = ["education:read", "education:create", "education:update", "education:delete"]


def url(name, **kw):
    return reverse(name, kwargs={"version": "v1", **kw})


def test_requires_auth_and_permission(api_client, auth_client):
    post = PostFactory()
    for name, kw in [("post-list", {}), ("post-detail", {"pk": post.pk})]:
        assert_error(api_client.get(url(name, **kw)), 401)
        assert_error(auth_client([]).get(url(name, **kw)), 403)
    body = {"title": "T", "body": "B", "topic": "scams"}
    assert_error(auth_client(["education:read"]).post(url("post-list"), body, format="json"), 403)
    assert_error(
        auth_client(["education:read"]).patch(url("post-detail", pk=post.pk), {}, format="json"), 403
    )
    assert_error(auth_client(["education:read"]).delete(url("post-detail", pk=post.pk)), 403)


def test_crud_publish_flow(auth_client):
    client = auth_client(ALL)
    created = client.post(
        url("post-list"), {"title": "Novo guia", "body": "Texto", "topic": "credentials"}, format="json"
    )
    assert created.status_code == 201, created.content
    assert created.data["status"] == "draft" and created.data["slug"] == "novo-guia"
    assert created.data["published_at"] is None
    assert Post.objects.get().created_by == client.user

    detail = url("post-detail", pk=created.data["id"])
    published = client.patch(detail, {"status": "published"}, format="json")
    assert published.data["status"] == "published" and published.data["published_at"]
    assert client.get(detail).data["title"] == "Novo guia"
    assert client.delete(detail).status_code == 204
    assert not Post.objects.exists()


def test_validation_and_404(auth_client):
    client = auth_client(ALL)
    assert_error(client.post(url("post-list"), {"title": "x"}, format="json"), 400, "validation_error")
    assert_error(
        client.post(url("post-list"), {"title": "x", "body": "y", "topic": "nope"}, format="json"),
        400,
        "validation_error",
    )
    assert_error(client.get(url("post-detail", pk="00000000-0000-0000-0000-000000000000")), 404)


def test_private_list_includes_drafts_filters_and_queries(auth_client, django_assert_max_num_queries):
    PostFactory.create_batch(4, status=PostStatus.PUBLISHED)
    PostFactory.create_batch(3, status=PostStatus.DRAFT)
    client = auth_client(["education:read"])
    with django_assert_max_num_queries(3):
        assert_paginated(client.get(url("post-list")), count=7)
    assert_paginated(client.get(url("post-list"), {"status": "draft"}), count=3)
