from django.contrib import admin
from django.utils import timezone

from apps.core.admin import AuditedAdmin
from apps.occurrences.constants import OccurrenceStatus
from apps.occurrences.models import LostDocumentOccurrence


@admin.register(LostDocumentOccurrence)
class LostDocumentOccurrenceAdmin(AuditedAdmin):
    """Ocorrências de documentos perdidos. A referência é gerada; `closed_at` acompanha o estado."""

    list_display = (
        "reference",
        "document_type",
        "document_number",
        "owner_name",
        "station_name",
        "status",
        "lost_at",
    )
    list_filter = ("status", "document_type", "lost_at")
    search_fields = ("reference", "document_number", "owner_name")
    list_select_related = ("created_by",)
    date_hierarchy = "lost_at"
    readonly_fields = ("reference", "closed_at")

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            obj.closed_at = timezone.now() if obj.status == OccurrenceStatus.CLOSED else None
        super().save_model(request, obj, form, change)
