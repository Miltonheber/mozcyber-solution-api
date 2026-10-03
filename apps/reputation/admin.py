from django.contrib import admin, messages

from apps.core.admin import AuditedAdmin, ReadOnlyAdmin
from apps.reputation.constants import NumberStatus, ReportStatus
from apps.reputation.models import MessageClassification, NumberReport, PhoneNumber
from apps.reputation.services import PhoneNumberService, ReportService


@admin.register(PhoneNumber)
class PhoneNumberAdmin(AuditedAdmin):
    """Reputação dos números. O estado só muda por acções (passam pelo service, que mantém score e contadores)."""

    list_display = (
        "number",
        "status",
        "category",
        "risk_score",
        "report_count",
        "fraud_count",
        "last_reported_at",
    )
    list_filter = ("status", "category")
    search_fields = ("number",)
    actions = ("mark_blacklisted", "mark_suspicious", "mark_cleared")
    readonly_fields = (
        "number",
        "status",
        "risk_score",
        "report_count",
        "classification_count",
        "fraud_count",
        "first_seen_at",
        "last_reported_at",
        "blacklisted_at",
    )

    def has_add_permission(self, request):
        return False  # os números nascem de classificações e denúncias

    def _moderate(self, request, queryset, status):
        service = PhoneNumberService()
        for phone in queryset:
            service.update(phone, {"status": status}, actor=request.user)
        self.message_user(request, f"{queryset.count()} número(s) actualizado(s).", messages.SUCCESS)

    @admin.action(description="Colocar na lista negra")
    def mark_blacklisted(self, request, queryset):
        self._moderate(request, queryset, NumberStatus.BLACKLISTED)

    @admin.action(description="Marcar como suspeito")
    def mark_suspicious(self, request, queryset):
        self._moderate(request, queryset, NumberStatus.SUSPICIOUS)

    @admin.action(description="Limpar (zera o risco e rejeita as denúncias activas)")
    def mark_cleared(self, request, queryset):
        self._moderate(request, queryset, NumberStatus.CLEARED)


@admin.register(NumberReport)
class NumberReportAdmin(AuditedAdmin):
    """Denúncias públicas. Só a moderação (estado e nota) é editável; rejeitar recalcula a reputação."""

    list_display = ("phone_number", "category", "channel", "status", "created_at")
    list_filter = ("status", "category", "channel")
    search_fields = ("phone_number__number", "behavior")
    list_select_related = ("phone_number",)
    date_hierarchy = "created_at"
    actions = ("confirm_reports", "reject_reports")
    submitted_fields = (
        "phone_number",
        "category",
        "behavior",
        "channel",
        "amount_lost",
        "reporter_contact",
        "reporter_ip",
    )

    def get_readonly_fields(self, request, obj=None):
        return (*super().get_readonly_fields(request, obj), *self.submitted_fields)

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change and "status" in form.changed_data:
            PhoneNumberService().register_activity(obj.phone_number.number)

    def _set_status(self, request, queryset, status):
        service = ReportService()
        for report in queryset:
            service.update(report, {"status": status}, actor=request.user)
        self.message_user(request, f"{queryset.count()} denúncia(s) actualizada(s).", messages.SUCCESS)

    @admin.action(description="Confirmar denúncias")
    def confirm_reports(self, request, queryset):
        self._set_status(request, queryset, ReportStatus.CONFIRMED)

    @admin.action(description="Rejeitar denúncias")
    def reject_reports(self, request, queryset):
        self._set_status(request, queryset, ReportStatus.REJECTED)


@admin.register(MessageClassification)
class MessageClassificationAdmin(ReadOnlyAdmin):
    list_display = ("phone_number", "verdict", "category", "confidence", "provider", "created_at")
    list_filter = ("verdict", "category", "provider")
    search_fields = ("phone_number__number", "message")
    list_select_related = ("phone_number",)
    date_hierarchy = "created_at"
