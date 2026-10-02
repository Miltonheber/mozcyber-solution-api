from apps.audit_log.serializers import ActionLogSerializer
from apps.audit_log.services import LogService
from apps.core.permissions import require_permissions
from apps.core.views import BaseAPIView, ListMixin


class ActionLogListView(ListMixin, BaseAPIView):
    """GET /logs/?user_id=&action=&resource_type=&resource_id=&search=&page=&size="""

    service_class = LogService
    read_serializer_class = ActionLogSerializer

    @require_permissions("log:read")
    def get(self, request, *args, **kwargs):
        return self.list(request)
