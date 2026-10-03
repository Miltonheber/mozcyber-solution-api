from apps.audit_log.mixins import LoggingMixin
from apps.core.permissions import require_permissions
from apps.core.views import BaseAPIView, CreateMixin, ListMixin, RetrieveMixin, UpdateMixin
from apps.occurrences.serializers import OccurrenceReadSerializer, OccurrenceWriteSerializer
from apps.occurrences.services import OccurrenceService


class OccurrenceListCreateView(LoggingMixin, ListMixin, CreateMixin, BaseAPIView):
    service_class = OccurrenceService
    read_serializer_class = OccurrenceReadSerializer
    write_serializer_class = OccurrenceWriteSerializer
    log_actions = {"POST": "occurrence.create"}
    log_resource_type = "occurrence"

    @require_permissions("occurrence:read")
    def get(self, request, *args, **kwargs):
        return self.list(request)

    @require_permissions("occurrence:create")
    def post(self, request, *args, **kwargs):
        return self.create(request)


class OccurrenceDetailView(LoggingMixin, RetrieveMixin, UpdateMixin, BaseAPIView):
    service_class = OccurrenceService
    read_serializer_class = OccurrenceReadSerializer
    write_serializer_class = OccurrenceWriteSerializer
    log_actions = {"PATCH": "occurrence.update"}
    log_resource_type = "occurrence"

    @require_permissions("occurrence:read")
    def get(self, request, pk, *args, **kwargs):
        return self.retrieve(request, pk)

    @require_permissions("occurrence:update")
    def patch(self, request, pk, *args, **kwargs):
        return self.partial_update(request, pk)
