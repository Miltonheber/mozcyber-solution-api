from apps.core.services import BaseService
from apps.education.repositories import PostRepository


class PostService(BaseService):
    """Gestão de conteúdo educativo (zona privada). Rascunhos incluídos."""

    repository_class = PostRepository


class PublicPostService(PostService):
    """Leitura pública: só publicações `published`."""

    def list(self, params=None):
        return self.repository.list_published(params)

    def get_by_slug(self, slug: str):
        return self.repository.get_published_by_slug(slug)
