from apps.core.services import BaseService
from apps.reputation.constants import ReportStatus
from apps.reputation.repositories import NumberReportRepository
from apps.reputation.services.phone_number_service import PhoneNumberService


class ReportService(BaseService):
    repository_class = NumberReportRepository

    def __init__(self, repository=None, phones=None):
        super().__init__(repository)
        self.phones = phones or PhoneNumberService()

    def report(self, number: str, data: dict, ip: str | None = None, actor=None):
        """Regista a denúncia e alimenta a reputação (blacklist ao atingir o limiar)."""
        phone = self.phones.repository.get_or_create_by_number(number)
        report = self.repository.create(actor=actor, phone_number=phone, reporter_ip=ip, **data)
        self.phones.register_activity(number, category=report.category, reported=True)
        return self.repository.get(report.pk)

    def update(self, instance, data: dict, actor=None):
        """Moderação: ao rejeitar uma denúncia, a reputação do número é recalculada."""
        was_rejected = instance.status == ReportStatus.REJECTED
        number = instance.phone_number.number
        updated = super().update(instance, data, actor=actor)
        if not was_rejected and updated.status == ReportStatus.REJECTED:
            self.phones.register_activity(number)
        return updated
