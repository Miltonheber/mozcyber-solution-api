from apps.audit_log.mixins import LoggingMixin
from apps.core.permissions import require_permissions
from apps.core.views import BaseAPIView, ListMixin, RetrieveMixin, UpdateMixin
from apps.reputation.serializers import (
    NumberReportModerationSerializer,
    NumberReportReadSerializer,
    PhoneNumberModerationSerializer,
    PhoneNumberReadSerializer,
)
from apps.reputation.services import PhoneNumberService, ReportService


class BlacklistListView(ListMixin, BaseAPIView):
    service_class = PhoneNumberService
    read_serializer_class = PhoneNumberReadSerializer

    @require_permissions("blacklist:read")
    def get(self, request, *args, **kwargs):
        return self.list(request)


class BlacklistDetailView(LoggingMixin, RetrieveMixin, UpdateMixin, BaseAPIView):
    service_class = PhoneNumberService
    read_serializer_class = PhoneNumberReadSerializer
    write_serializer_class = PhoneNumberModerationSerializer
    log_actions = {"PATCH": "blacklist.update"}
    log_resource_type = "phone_number"

    @require_permissions("blacklist:read")
    def get(self, request, pk, *args, **kwargs):
        return self.retrieve(request, pk)

    @require_permissions("blacklist:update")
    def patch(self, request, pk, *args, **kwargs):
        return self.partial_update(request, pk)


class ReportListView(ListMixin, BaseAPIView):
    service_class = ReportService
    read_serializer_class = NumberReportReadSerializer

    @require_permissions("report:read")
    def get(self, request, *args, **kwargs):
        return self.list(request)


class ReportDetailView(LoggingMixin, RetrieveMixin, UpdateMixin, BaseAPIView):
    service_class = ReportService
    read_serializer_class = NumberReportReadSerializer
    write_serializer_class = NumberReportModerationSerializer
    log_actions = {"PATCH": "report.update"}
    log_resource_type = "number_report"

    @require_permissions("report:read")
    def get(self, request, pk, *args, **kwargs):
        return self.retrieve(request, pk)

    @require_permissions("report:update")
    def patch(self, request, pk, *args, **kwargs):
        return self.partial_update(request, pk)
