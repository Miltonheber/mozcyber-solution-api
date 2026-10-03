from unittest.mock import MagicMock

from apps.education.services import PublicPostService


def test_public_service_only_asks_for_published_without_db():
    repo = MagicMock()
    service = PublicPostService(repository=repo)
    service.list({"topic": "scams"})
    repo.list_published.assert_called_once_with({"topic": "scams"})
    service.get_by_slug("x")
    repo.get_published_by_slug.assert_called_once_with("x")
