from apps.core.services import BaseService
from apps.user.repositories import ProfileRepository


class ProfileService(BaseService):
    repository_class = ProfileRepository
