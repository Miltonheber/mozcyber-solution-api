from apps.core.services import BaseService
from apps.user.repositories import PermissionRepository


class PermissionService(BaseService):
    repository_class = PermissionRepository
