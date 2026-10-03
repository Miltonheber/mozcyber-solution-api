from apps.user.constants import ADMIN_PROFILE_CODE, PERMISSION_CATALOG, SEED_PROFILES
from apps.user.models import Permission, Profile


def seed_access() -> Profile:
    """Idempotente: cria permissões do catálogo, o perfil admin (todas) e os perfis operacionais."""
    permissions = []
    for code, description in PERMISSION_CATALOG.items():
        permission, _ = Permission.objects.get_or_create(
            code=code, defaults={"name": code, "description": description}
        )
        permissions.append(permission)
    admin, _ = Profile.objects.get_or_create(code=ADMIN_PROFILE_CODE, defaults={"name": "Administrador"})
    admin.permissions.set(permissions)
    by_code = {p.code: p for p in permissions}
    for code, (name, perm_codes) in SEED_PROFILES.items():
        profile, _ = Profile.objects.get_or_create(code=code, defaults={"name": name})
        profile.permissions.set([by_code[c] for c in perm_codes])
    return admin
