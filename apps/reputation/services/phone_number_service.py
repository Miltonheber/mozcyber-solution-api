from django.utils import timezone

from apps.core.services import BaseService
from apps.reputation.constants import NumberStatus
from apps.reputation.models import PhoneNumber
from apps.reputation.repositories import NumberReportRepository, PhoneNumberRepository
from apps.reputation.utils.scoring import compute_reputation


class PhoneNumberService(BaseService):
    repository_class = PhoneNumberRepository

    def __init__(self, repository=None, reports=None):
        super().__init__(repository)
        self.reports = reports or NumberReportRepository()

    def reputation(self, number: str) -> PhoneNumber:
        """Reputação pública; número nunca visto => instância não gravada com os defaults (`unknown`)."""
        return self.repository.find_by_number(number) or PhoneNumber(number=number)

    def register_activity(self, number: str, *, category=None, high_confidence_fraud=False, reported=False):
        """Recalcula contadores, score e estado depois de uma classificação ou denúncia."""
        phone = self.repository.get_or_create_by_number(number)
        counters = self.repository.counters(phone)
        score, status = compute_reputation(
            reports=counters["report_count"],
            frauds=counters["fraud_count"],
            current_status=phone.status,
            high_confidence_fraud=high_confidence_fraud,
        )
        fields = {**counters, "risk_score": score, "status": status}
        if category:
            fields["category"] = category
        if reported:
            fields["last_reported_at"] = timezone.now()
        if status == NumberStatus.BLACKLISTED and phone.blacklisted_at is None:
            fields["blacklisted_at"] = timezone.now()
        return self.repository.update(phone, **fields)

    def update(self, instance, data: dict, actor=None):
        """Moderação. `cleared` limpa o número: zera o score, rejeita as denúncias e tira-o da blacklist."""
        if data.get("status") == NumberStatus.CLEARED:
            self.reports.reject_all_for(instance)
            data = {**data, "risk_score": 0, "report_count": 0, "blacklisted_at": None}
        elif data.get("status") == NumberStatus.BLACKLISTED and instance.blacklisted_at is None:
            data = {**data, "blacklisted_at": timezone.now()}
        return super().update(instance, data, actor=actor)
