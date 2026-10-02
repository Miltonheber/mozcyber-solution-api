from apps.user.models import Permission, Profile


def get_user_permissions(user) -> list[str]:
    """Códigos de permissão efectivos do utilizador (via perfis activos). Uma única query."""
    return sorted(
        Permission.objects.filter(is_active=True, profiles__is_active=True, profiles__users=user)
        .values_list("code", flat=True)
        .distinct()
    )


def get_user_profiles(user) -> list[str]:
    """Códigos dos perfis activos do utilizador. Uma única query."""
    return sorted(Profile.objects.filter(is_active=True, users=user).values_list("code", flat=True))
