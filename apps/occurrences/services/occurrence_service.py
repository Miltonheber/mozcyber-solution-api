from django.utils import timezone

from apps.core.services import BaseService
from apps.occurrences.constants import OccurrenceStatus
from apps.occurrences.repositories import OccurrenceRepository


class OccurrenceService(BaseService):
    repository_class = OccurrenceRepository

    def update(self, instance, data: dict, actor=None):
        """Fechar a ocorrência regista `closed_at`; reabri-la limpa-o."""
        if "status" in data:
            closed = data["status"] == OccurrenceStatus.CLOSED
            data = {**data, "closed_at": timezone.now() if closed else None}
        return super().update(instance, data, actor=actor)
