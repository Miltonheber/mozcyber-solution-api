import pytest

from apps.core.exceptions import NotFoundException
from apps.user.repositories import UserRepository
from apps.user.tests.factories import ProfileFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_get_unknown_or_invalid_pk_raises_not_found():
    repo = UserRepository()
    with pytest.raises(NotFoundException):
        repo.get("00000000-0000-0000-0000-000000000000")
    with pytest.raises(NotFoundException):
        repo.get("not-a-uuid")


def test_list_filters_and_search():
    UserFactory(email="alice@example.com", name="Alice")
    UserFactory(email="bob@example.com", name="Bob", is_active=False)
    repo = UserRepository()
    assert [u.email for u in repo.list({"search": "ali"})] == ["alice@example.com"]
    assert [u.email for u in repo.list({"is_active": "False"})] == ["bob@example.com"]
    assert repo.list({"unknown": "x"}).count() == 2  # filtros fora da whitelist são ignorados


def test_create_sets_authorship_and_m2m():
    actor = UserFactory()
    profile = ProfileFactory()
    user = UserRepository().create(actor=actor, email="n@example.com", profiles=[profile])
    assert user.created_by == actor and user.updated_by == actor
    assert list(user.profiles.all()) == [profile]
