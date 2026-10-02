import pytest
from rest_framework_simplejwt.tokens import AccessToken

from apps.core.testing.helpers import grant_permissions
from apps.user.tests.factories import PermissionFactory, ProfileFactory, UserFactory
from apps.user.utils.permissions import get_user_permissions, get_user_profiles
from apps.user.utils.seed import seed_access
from apps.user.utils.tokens import build_tokens

pytestmark = pytest.mark.django_db


def test_permissions_aggregated_distinct_and_only_active(django_assert_num_queries):
    user = UserFactory()
    p1, p2 = PermissionFactory(code="a:read"), PermissionFactory(code="b:read")
    inactive = PermissionFactory(code="c:read", is_active=False)
    profile1 = ProfileFactory(code="p1")
    profile2 = ProfileFactory(code="p2")
    profile1.permissions.set([p1, p2, inactive])
    profile2.permissions.set([p1])
    user.profiles.set([profile1, profile2])
    with django_assert_num_queries(1):
        assert get_user_permissions(user) == ["a:read", "b:read"]
    with django_assert_num_queries(1):
        assert get_user_profiles(user) == ["p1", "p2"]


def test_inactive_profile_grants_nothing():
    user = UserFactory()
    profile = ProfileFactory(is_active=False)
    profile.permissions.add(PermissionFactory(code="x:read"))
    user.profiles.add(profile)
    assert get_user_permissions(user) == []


def test_token_contains_custom_claims():
    user = grant_permissions(UserFactory(), ["user:read"])
    token = AccessToken(build_tokens(user)["access"])
    assert token["permissions"] == ["user:read"]
    assert token["profiles"] == [f"test-{user.pk}"]


def test_seed_access_is_idempotent_and_admin_gets_everything():
    from apps.user.constants import PERMISSION_CATALOG

    seed_access()
    admin = seed_access()
    assert admin.permissions.count() == len(PERMISSION_CATALOG)
