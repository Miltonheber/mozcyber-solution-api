from django.contrib.auth.hashers import make_password

from apps.core.services import BaseService
from apps.user.repositories import UserRepository


class UserService(BaseService):
    repository_class = UserRepository

    def create(self, data: dict, actor=None):
        data = {**data, "password": make_password(data["password"])}
        return super().create(data, actor)

    def update(self, instance, data: dict, actor=None):
        if "password" in data:
            data = {**data, "password": make_password(data["password"])}
        return super().update(instance, data, actor)
