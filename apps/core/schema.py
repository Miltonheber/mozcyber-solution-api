from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import OpenApiParameter

from .views import ListMixin


class BaseAutoSchema(AutoSchema):
    """Gera o OpenAPI das `BaseAPIView` a partir de `read_/write_serializer_class` (APIView não tem serializer_class).

    Views fora deste padrão (ex.: login) usam `@extend_schema` normalmente.
    """

    def _is_list(self) -> bool:
        return self.method == "GET" and isinstance(self.view, ListMixin)

    def _is_list_view(self, serializer=None):
        return self._is_list() or super()._is_list_view(serializer)

    def get_request_serializer(self):
        write = getattr(self.view, "write_serializer_class", None)
        if write and self.method in ("POST", "PUT", "PATCH"):
            return write
        return super().get_request_serializer()

    def get_response_serializers(self):
        read = getattr(self.view, "read_serializer_class", None)
        if read is None:
            return super().get_response_serializers()
        if self.method == "DELETE":
            return {204: None}
        if self._is_list():
            return read(many=True)
        return {201: read} if self.method == "POST" else read

    def get_override_parameters(self):
        if not self._is_list():
            return []
        repo = getattr(getattr(self.view, "service_class", None), "repository_class", None)
        fields = getattr(repo, "filter_fields", ())
        params = [OpenApiParameter(f, str, description="Filtro exacto") for f in fields]
        if getattr(repo, "search_fields", ()):
            params.append(
                OpenApiParameter("search", str, description="Pesquisa em: " + ", ".join(repo.search_fields))
            )
        return params
