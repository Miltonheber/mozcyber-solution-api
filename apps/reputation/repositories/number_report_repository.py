from apps.core.repositories import BaseRepository
from apps.reputation.constants import ReportStatus
from apps.reputation.models import NumberReport


class NumberReportRepository(BaseRepository[NumberReport]):
    model = NumberReport
    select_related = ("phone_number",)
    filter_fields = ("status", "category", "channel", "phone_number__number")
    search_fields = ("phone_number__number", "behavior")

    def reject_all_for(self, phone) -> int:
        """Rejeita as denúncias activas de um número (usado ao limpar o número na moderação)."""
        return phone.reports.exclude(status=ReportStatus.REJECTED).update(status=ReportStatus.REJECTED)
