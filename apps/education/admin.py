from django.contrib import admin

from apps.core.admin import AuditedAdmin
from apps.education.models import Post


@admin.register(Post)
class PostAdmin(AuditedAdmin):
    """Conteúdo educativo. O slug é gerado a partir do título se ficar vazio; `published_at` na 1ª publicação."""

    list_display = ("title", "topic", "status", "published_at", "updated_at")
    list_filter = ("status", "topic")
    search_fields = ("title", "summary")
    date_hierarchy = "created_at"
    readonly_fields = ("published_at",)
