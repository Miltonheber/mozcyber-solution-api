from apps.user.constants import ADMIN_PROFILE_CODE, PERMISSION_CATALOG
from apps.user.models import Permission, Profile


def seed_access() -> Profile:
    """Idempotente: cria permissões do catálogo e o perfil admin com todas elas."""
    permissions = []
    for code, description in PERMISSION_CATALOG.items():
        permission, _ = Permission.objects.get_or_create(
            code=code, defaults={"name": code, "description": description}
        )
        permissions.append(permission)
    admin, _ = Profile.objects.get_or_create(code=ADMIN_PROFILE_CODE, defaults={"name": "Administrador"})
    admin.permissions.set(permissions)
    return admin
