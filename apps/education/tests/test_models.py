import pytest

from apps.education.constants import PostStatus
from apps.education.tests.factories import PostFactory

pytestmark = pytest.mark.django_db


def test_slug_is_generated_and_unique():
    a = PostFactory(title="Cuidado com o SIM swap")
    b = PostFactory(title="Cuidado com o SIM swap")
    assert a.slug == "cuidado-com-o-sim-swap"
    assert b.slug == "cuidado-com-o-sim-swap-2"


def test_slug_is_stable_on_update():
    post = PostFactory(title="Original")
    post.title = "Novo título"
    post.save()
    assert post.slug == "original"


def test_published_at_set_when_published():
    draft = PostFactory()
    assert draft.status == PostStatus.DRAFT and draft.published_at is None
    published = PostFactory(status=PostStatus.PUBLISHED)
    assert published.published_at is not None
