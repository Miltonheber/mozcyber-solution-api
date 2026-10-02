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
from apps.user.serializers import ProfileReadSerializer, ProfileWriteSerializer
from apps.user.services import ProfileService


class ProfileListCreateView(LoggingMixin, ListMixin, CreateMixin, BaseAPIView):
    service_class = ProfileService
    read_serializer_class = ProfileReadSerializer
    write_serializer_class = ProfileWriteSerializer
    log_actions = {"POST": "profile.create"}
    log_resource_type = "profile"

    @require_permissions("profile:read")
    def get(self, request, *args, **kwargs):
        return self.list(request)

    @require_permissions("profile:create")
    def post(self, request, *args, **kwargs):
        return self.create(request)


class ProfileDetailView(LoggingMixin, RetrieveMixin, UpdateMixin, DestroyMixin, BaseAPIView):
    service_class = ProfileService
    read_serializer_class = ProfileReadSerializer
    write_serializer_class = ProfileWriteSerializer
    log_actions = {"PATCH": "profile.update", "DELETE": "profile.delete"}
    log_resource_type = "profile"

    @require_permissions("profile:read")
    def get(self, request, pk, *args, **kwargs):
        return self.retrieve(request, pk)

    @require_permissions("profile:update")
    def patch(self, request, pk, *args, **kwargs):
        return self.partial_update(request, pk)

    @require_permissions("profile:delete")
    def delete(self, request, pk, *args, **kwargs):
        return self.destroy(request, pk)
