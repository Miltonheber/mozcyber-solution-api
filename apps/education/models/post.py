from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from apps.core.models import BaseModel
from apps.education.constants import PostStatus, Topic


class Post(BaseModel):
    """Conteúdo educativo. Leitura pública apenas de `published`."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    summary = models.CharField(max_length=500, blank=True)
    body = models.TextField()
    topic = models.CharField(max_length=30, choices=Topic.choices)
    status = models.CharField(max_length=20, choices=PostStatus.choices, default=PostStatus.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    cover_image_url = models.URLField(blank=True)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["status", "topic"])]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        if self.status == PostStatus.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def _unique_slug(self) -> str:
        base = slugify(self.title)[:200] or "post"
        slug, n = base, 2
        while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug, n = f"{base}-{n}", n + 1
        return slug

    def __str__(self):
        return self.title
