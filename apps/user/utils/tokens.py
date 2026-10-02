from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.permissions import PERMISSIONS_CLAIM, PROFILES_CLAIM

from .permissions import get_user_permissions, get_user_profiles


def build_tokens(user) -> dict:
    """Gera refresh+access com as claims `profiles` e `permissions` (access herda as claims do refresh)."""
    refresh = RefreshToken.for_user(user)
    refresh[PROFILES_CLAIM] = get_user_profiles(user)
    refresh[PERMISSIONS_CLAIM] = get_user_permissions(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}
