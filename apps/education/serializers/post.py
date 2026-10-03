from rest_framework import serializers

from apps.education.models import Post


class PostListSerializer(serializers.ModelSerializer):
    """Listagem pública: sem o corpo do texto."""

    class Meta:
        model = Post
        fields = ("id", "title", "slug", "summary", "topic", "cover_image_url", "published_at")
        read_only_fields = fields


class PostPublicDetailSerializer(PostListSerializer):
    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ("body",)
        read_only_fields = fields


class PostReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = (
            "id",
            "title",
            "slug",
            "summary",
            "body",
            "topic",
            "status",
            "cover_image_url",
            "published_at",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class PostWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("title", "summary", "body", "topic", "status", "cover_image_url")
