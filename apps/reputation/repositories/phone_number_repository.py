from apps.core.repositories import BaseRepository
from apps.reputation.constants import ReportStatus, Verdict
from apps.reputation.models import PhoneNumber


class PhoneNumberRepository(BaseRepository[PhoneNumber]):
    model = PhoneNumber
    filter_fields = ("status", "category")
    search_fields = ("number",)

    def find_by_number(self, number: str) -> PhoneNumber | None:
        return self.get_queryset().filter(number=number).first()

    def get_or_create_by_number(self, number: str) -> PhoneNumber:
        phone, _ = self.model.objects.get_or_create(number=number)
        return phone

    def counters(self, phone: PhoneNumber) -> dict[str, int]:
        """Contadores autoritativos, recontados a partir dos registos (denúncias rejeitadas não contam)."""
        classifications = phone.classifications
        return {
            "report_count": phone.reports.exclude(status=ReportStatus.REJECTED).count(),
            "classification_count": classifications.count(),
            "fraud_count": classifications.filter(verdict=Verdict.FRAUD).count(),
        }
