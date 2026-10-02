from apps.core.repositories import BaseRepository
from apps.user.models import Permission


class PermissionRepository(BaseRepository[Permission]):
    model = Permission
    search_fields = ("code", "name")
