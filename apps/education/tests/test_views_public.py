import pytest
from django.urls import reverse
from rest_framework.throttling import ScopedRateThrottle

from apps.core.testing.helpers import assert_error, assert_paginated
from apps.education.constants import PostStatus, Topic
from apps.education.tests.factories import PostFactory

pytestmark = pytest.mark.django_db


def url(name, **kw):
    return reverse(name, kwargs={"version": "v1", **kw})


def test_public_list_is_open_and_hides_drafts(api_client):
    PostFactory.create_batch(3, status=PostStatus.PUBLISHED)
    PostFactory.create_batch(2, status=PostStatus.DRAFT)
    response = api_client.get(url("public-post-list"))
    assert_paginated(response, count=3)
    assert "body" not in response.data["results"][0]  # listagem sem corpo


def test_public_list_filters_and_search(api_client):
    PostFactory(status=PostStatus.PUBLISHED, topic=Topic.SIM_SWAP, title="Troca de SIM explicada")
    PostFactory(status=PostStatus.PUBLISHED, topic=Topic.SCAMS, title="Burlas por SMS")
    assert_paginated(api_client.get(url("public-post-list"), {"topic": "sim_swap"}), count=1)
    assert_paginated(api_client.get(url("public-post-list"), {"search": "burlas"}), count=1)
    # `status` não permite ver rascunhos pela via pública
    PostFactory(status=PostStatus.DRAFT)
    assert_paginated(api_client.get(url("public-post-list"), {"status": "draft"}), count=0)


def test_public_list_newest_first_and_paginated(api_client):
    PostFactory.create_batch(5, status=PostStatus.PUBLISHED)
    response = api_client.get(url("public-post-list"), {"size": 2})
    assert_paginated(response, count=5, size=2)
    dates = [r["published_at"] for r in response.data["results"]]
    assert dates == sorted(dates, reverse=True)


def test_public_list_constant_queries(api_client, django_assert_max_num_queries):
    PostFactory.create_batch(12, status=PostStatus.PUBLISHED)
    with django_assert_max_num_queries(3):
        assert_paginated(api_client.get(url("public-post-list")), count=12)


def test_public_detail_by_slug_includes_body(api_client):
    post = PostFactory(status=PostStatus.PUBLISHED, title="Guia", body="Texto completo")
    response = api_client.get(url("public-post-detail", slug=post.slug))
    assert response.status_code == 200 and response.data["body"] == "Texto completo"
    assert "status" not in response.data


def test_public_detail_draft_or_unknown_is_404(api_client):
    draft = PostFactory(status=PostStatus.DRAFT)
    assert_error(api_client.get(url("public-post-detail", slug=draft.slug)), 404, "post_not_found")
    assert_error(api_client.get(url("public-post-detail", slug="nao-existe")), 404, "post_not_found")


def test_public_posts_are_throttled(api_client, monkeypatch):
    monkeypatch.setitem(ScopedRateThrottle.THROTTLE_RATES, "public_read", "2/min")
    assert api_client.get(url("public-post-list")).status_code == 200
    assert api_client.get(url("public-post-list")).status_code == 200
    assert_error(api_client.get(url("public-post-list")), 429, "throttled")
