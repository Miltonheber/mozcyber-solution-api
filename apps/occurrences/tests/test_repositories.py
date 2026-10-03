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


def _dated(**kw):
    from apps.occurrences.tests.factories import LostDocumentOccurrenceFactory

    return LostDocumentOccurrenceFactory(**kw)


@pytest.mark.django_db
def test_lost_at_range_is_inclusive_and_combines_with_filters():
    import datetime

    from apps.occurrences.repositories import OccurrenceRepository

    old = _dated(lost_at=datetime.date(2026, 1, 10))
    mid = _dated(lost_at=datetime.date(2026, 3, 15), status="found")
    _dated(lost_at=datetime.date(2026, 6, 1))
    repo = OccurrenceRepository()
    both = repo.list({"lost_at_from": "2026-01-10", "lost_at_to": "2026-03-15"})
    assert set(both) == {old, mid}
    assert list(repo.list({"lost_at_from": "2026-02-01", "lost_at_to": "2026-04-01", "status": "found"})) == [
        mid
    ]
    assert repo.list({"lost_at_from": "2026-06-02"}).count() == 0


@pytest.mark.django_db
def test_created_range_with_whole_day_and_datetime():
    from django.utils import timezone

    from apps.occurrences.repositories import OccurrenceRepository

    occ = _dated()
    today = timezone.localdate().isoformat()
    repo = OccurrenceRepository()
    assert list(repo.list({"created_from": today, "created_to": today})) == [occ]  # dia inteiro
    future = (timezone.now() + timezone.timedelta(hours=1)).isoformat()
    assert repo.list({"created_from": future}).count() == 0


@pytest.mark.django_db
def test_invalid_range_and_ordering_raise_400():
    from apps.core.exceptions import ValidationException
    from apps.occurrences.repositories import OccurrenceRepository

    repo = OccurrenceRepository()
    for params in (
        {"lost_at_from": "ontem"},
        {"created_to": "2026-13-45"},
        {"lost_at_from": "2026-05-02", "lost_at_to": "2026-05-01"},
        {"created_from": "2026-05-02", "created_to": "2026-05-01"},
        {"ordering": "owner_contact"},
    ):
        with pytest.raises(ValidationException) as exc:
            repo.list(params)
        assert exc.value.code == "invalid_filter"


@pytest.mark.django_db
def test_ordering_asc_desc_and_multiple():
    import datetime

    from apps.occurrences.repositories import OccurrenceRepository

    a = _dated(lost_at=datetime.date(2026, 1, 1))
    b = _dated(lost_at=datetime.date(2026, 2, 1))
    c = _dated(lost_at=datetime.date(2026, 2, 1))
    repo = OccurrenceRepository()
    assert list(repo.list({"ordering": "lost_at"}))[0] == a
    assert list(repo.list({"ordering": "-lost_at"}))[-1] == a
    assert {o.pk for o in list(repo.list({"ordering": "-lost_at,reference"}))[:2]} == {b.pk, c.pk}
