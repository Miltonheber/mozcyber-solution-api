from apps.core.exceptions import NotFoundException
from apps.core.repositories import BaseRepository
from apps.education.constants import PostStatus
from apps.education.models import Post


class PostRepository(BaseRepository[Post]):
    model = Post
    filter_fields = ("topic", "status")
    search_fields = ("title", "summary")

    def list_published(self, params=None):
        return self.list(params).filter(status=PostStatus.PUBLISHED).order_by("-published_at")

    def get_published_by_slug(self, slug: str) -> Post:
        post = self.get_queryset().filter(slug=slug, status=PostStatus.PUBLISHED).first()
        if post is None:
            raise NotFoundException("Publicação não encontrada.", code="post_not_found")
        return post
