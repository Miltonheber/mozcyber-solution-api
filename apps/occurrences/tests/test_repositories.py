import pytest

from apps.occurrences.models import LostDocumentOccurrence
from apps.occurrences.repositories import OccurrenceRepository
from apps.occurrences.tests.factories import LostDocumentOccurrenceFactory

pytestmark = pytest.mark.django_db

DATA = dict(
    document_type="bi",
    document_number="X1",
    owner_name="Ana",
    lost_at="2026-01-01",
    location="Baixa",
    station_name="Esq 1",
)


def test_create_retries_on_reference_collision(monkeypatch):
    existing = LostDocumentOccurrenceFactory()
    candidates = iter([existing.reference, existing.reference, "OC-2099-000001"])
    monkeypatch.setattr(LostDocumentOccurrence, "_next_reference", lambda self: next(candidates))
    created = OccurrenceRepository().create(**DATA)
    assert created.reference == "OC-2099-000001"
