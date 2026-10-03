from django.contrib import admin

from apps.audit_log.models import ActionLog
from apps.core.admin import ReadOnlyAdmin


@admin.register(ActionLog)
class ActionLogAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "action", "user", "method", "path", "status_code")
    list_filter = ("method", "status_code", "resource_type")
    search_fields = ("action", "path", "resource_id", "user__email")
    date_hierarchy = "created_at"
    list_select_related = ("user",)
