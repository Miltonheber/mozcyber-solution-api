import pytest
from django.utils import timezone

from apps.occurrences.constants import OccurrenceStatus
from apps.occurrences.tests.factories import LostDocumentOccurrenceFactory

pytestmark = pytest.mark.django_db


def test_reference_is_sequential_per_year():
    year = timezone.now().year
    first = LostDocumentOccurrenceFactory()
    second = LostDocumentOccurrenceFactory()
    assert first.reference == f"OC-{year}-000001"
    assert second.reference == f"OC-{year}-000002"


def test_reference_not_regenerated_on_update():
    occ = LostDocumentOccurrenceFactory()
    ref = occ.reference
    occ.status = OccurrenceStatus.FOUND
    occ.save()
    assert occ.reference == ref


def test_defaults():
    assert LostDocumentOccurrenceFactory().status == OccurrenceStatus.OPEN
