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
from apps.user.serializers import PermissionReadSerializer, PermissionWriteSerializer
from apps.user.services import PermissionService


class PermissionListCreateView(LoggingMixin, ListMixin, CreateMixin, BaseAPIView):
    service_class = PermissionService
    read_serializer_class = PermissionReadSerializer
    write_serializer_class = PermissionWriteSerializer
    log_actions = {"POST": "permission.create"}
    log_resource_type = "permission"

    @require_permissions("permission:read")
    def get(self, request, *args, **kwargs):
        return self.list(request)

    @require_permissions("permission:create")
    def post(self, request, *args, **kwargs):
        return self.create(request)


class PermissionDetailView(LoggingMixin, RetrieveMixin, UpdateMixin, DestroyMixin, BaseAPIView):
    service_class = PermissionService
    read_serializer_class = PermissionReadSerializer
    write_serializer_class = PermissionWriteSerializer
    log_actions = {"PATCH": "permission.update", "DELETE": "permission.delete"}
    log_resource_type = "permission"

    @require_permissions("permission:read")
    def get(self, request, pk, *args, **kwargs):
        return self.retrieve(request, pk)

    @require_permissions("permission:update")
    def patch(self, request, pk, *args, **kwargs):
        return self.partial_update(request, pk)

    @require_permissions("permission:delete")
    def delete(self, request, pk, *args, **kwargs):
        return self.destroy(request, pk)
