from django.db import IntegrityError, transaction

from apps.core.repositories import BaseRepository
from apps.occurrences.models import LostDocumentOccurrence

MAX_REFERENCE_ATTEMPTS = 5


class OccurrenceRepository(BaseRepository[LostDocumentOccurrence]):
    model = LostDocumentOccurrence
    select_related = ("created_by",)
    filter_fields = ("status", "document_type", "document_number", "station_name", "reference")
    search_fields = ("reference", "document_number", "owner_name")
    range_fields = {
        "lost_at_from": ("lost_at", "gte"),
        "lost_at_to": ("lost_at", "lte"),
        "created_from": ("created_at", "gte"),
        "created_to": ("created_at", "lte"),
    }
    ordering_fields = ("created_at", "updated_at", "lost_at", "reference", "closed_at")

    def create(self, *, actor=None, **data):
        """A referência é sequencial por ano; em corrida entre dois pedidos o índice único falha e repete-se."""
        for attempt in range(MAX_REFERENCE_ATTEMPTS):
            try:
                with transaction.atomic():
                    return super().create(actor=actor, **data)
            except IntegrityError:
                if attempt == MAX_REFERENCE_ATTEMPTS - 1:
                    raise
