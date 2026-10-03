from drf_spectacular.utils import extend_schema
from rest_framework.response import Response

from apps.audit_log.mixins import LoggingMixin
from apps.core.permissions import require_permissions
from apps.core.views import (
    BaseAPIView,
    CreateMixin,
    DestroyMixin,
    ListMixin,
    PublicAPIView,
    RetrieveMixin,
    UpdateMixin,
)
from apps.education.serializers import (
    PostListSerializer,
    PostPublicDetailSerializer,
    PostReadSerializer,
    PostWriteSerializer,
)
from apps.education.services import PostService, PublicPostService


class PublicPostListView(ListMixin, PublicAPIView):
    """Publicações educativas publicadas (sem login)."""

    throttle_scope = "public_read"
    service_class = PublicPostService
    read_serializer_class = PostListSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request)


class PublicPostDetailView(PublicAPIView):
    throttle_scope = "public_read"
    service_class = PublicPostService

    @extend_schema(responses=PostPublicDetailSerializer)
    def get(self, request, slug, *args, **kwargs):
        return Response(PostPublicDetailSerializer(self.service.get_by_slug(slug)).data)


class PostListCreateView(LoggingMixin, ListMixin, CreateMixin, BaseAPIView):
    service_class = PostService
    read_serializer_class = PostReadSerializer
    write_serializer_class = PostWriteSerializer
    log_actions = {"POST": "post.create"}
    log_resource_type = "post"

    @require_permissions("education:read")
    def get(self, request, *args, **kwargs):
        return self.list(request)

    @require_permissions("education:create")
    def post(self, request, *args, **kwargs):
        return self.create(request)


class PostDetailView(LoggingMixin, RetrieveMixin, UpdateMixin, DestroyMixin, BaseAPIView):
    service_class = PostService
    read_serializer_class = PostReadSerializer
    write_serializer_class = PostWriteSerializer
    log_actions = {"PATCH": "post.update", "DELETE": "post.delete"}
    log_resource_type = "post"

    @require_permissions("education:read")
    def get(self, request, pk, *args, **kwargs):
        return self.retrieve(request, pk)

    @require_permissions("education:update")
    def patch(self, request, pk, *args, **kwargs):
        return self.partial_update(request, pk)

    @require_permissions("education:delete")
    def delete(self, request, pk, *args, **kwargs):
        return self.destroy(request, pk)
