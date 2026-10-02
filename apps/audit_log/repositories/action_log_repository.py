from apps.audit_log.models import ActionLog
from apps.core.repositories import BaseRepository


class ActionLogRepository(BaseRepository[ActionLog]):
    model = ActionLog
    select_related = ("user",)
    filter_fields = ("user_id", "action", "resource_type", "resource_id", "method", "status_code")
    search_fields = ("action", "path")
