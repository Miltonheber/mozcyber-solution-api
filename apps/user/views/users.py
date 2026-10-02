from apps.audit_log.mixins import LoggingMixin
from apps.core.permissions import require_permissions
from apps.core.views import (
    BaseAPIView,
    CreateMixin,
    DestroyMixin,
    ListMixin,
    RetrieveMixin,
    UpdateMixin,
)
from apps.user.serializers import UserReadSerializer, UserWriteSerializer
from apps.user.services import UserService


class UserListCreateView(LoggingMixin, ListMixin, CreateMixin, BaseAPIView):
    service_class = UserService
    read_serializer_class = UserReadSerializer
    write_serializer_class = UserWriteSerializer
    log_actions = {"POST": "user.create"}
    log_resource_type = "user"

    @require_permissions("user:read")
    def get(self, request, *args, **kwargs):
        return self.list(request)

    @require_permissions("user:create")
    def post(self, request, *args, **kwargs):
        return self.create(request)


class UserDetailView(LoggingMixin, RetrieveMixin, UpdateMixin, DestroyMixin, BaseAPIView):
    service_class = UserService
    read_serializer_class = UserReadSerializer
    write_serializer_class = UserWriteSerializer
    log_actions = {"PATCH": "user.update", "DELETE": "user.delete"}
    log_resource_type = "user"

    @require_permissions("user:read")
    def get(self, request, pk, *args, **kwargs):
        return self.retrieve(request, pk)

    @require_permissions("user:update")
    def patch(self, request, pk, *args, **kwargs):
        return self.partial_update(request, pk)

    @require_permissions("user:delete")
    def delete(self, request, pk, *args, **kwargs):
        return self.destroy(request, pk)
