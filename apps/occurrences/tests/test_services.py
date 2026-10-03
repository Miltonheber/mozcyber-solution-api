from unittest.mock import MagicMock

from apps.occurrences.services import OccurrenceService


def test_closing_sets_closed_at_and_reopening_clears_it_without_db():
    repo = MagicMock()
    service = OccurrenceService(repository=repo)
    service.update(MagicMock(), {"status": "closed"})
    assert repo.update.call_args.kwargs["closed_at"] is not None
    service.update(MagicMock(), {"status": "open"})
    assert repo.update.call_args.kwargs["closed_at"] is None
    service.update(MagicMock(), {"location": "Baixa"})
    assert "closed_at" not in repo.update.call_args.kwargs
