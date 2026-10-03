from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel
from apps.occurrences.constants import DocumentType, OccurrenceStatus
from apps.occurrences.utils.reference import build_reference, parse_sequence


class LostDocumentOccurrence(BaseModel):
    """Ocorrência de documento perdido, criada por um utilizador do perfil esquadra (`created_by`)."""

    reference = models.CharField(max_length=20, unique=True, editable=False)
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    document_number = models.CharField(max_length=50, db_index=True)
    owner_name = models.CharField(max_length=200)
    owner_contact = models.CharField(max_length=100, blank=True)
    lost_at = models.DateField()
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=OccurrenceStatus.choices, default=OccurrenceStatus.OPEN)
    station_name = models.CharField(max_length=200)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=["document_type", "document_number"]),
            models.Index(fields=["status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._next_reference()
        super().save(*args, **kwargs)

    def _next_reference(self) -> str:
        year = timezone.now().year
        last = (
            type(self)
            .objects.filter(reference__startswith=f"OC-{year}-")
            .order_by("-reference")
            .values_list("reference", flat=True)
        ).first()
        return build_reference(year, parse_sequence(last) + 1 if last else 1)

    def __str__(self):
        return self.reference
