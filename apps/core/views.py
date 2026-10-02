from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .pagination import StandardPagination
from .permissions import HasPermission


class BaseAPIView(APIView):
    """Base de todas as views. Subclasses declaram `service_class`, serializers e, em cada método HTTP, `@require_permissions`.

    Views devem ser finas: validar entrada (serializer) -> chamar service -> serializar saída.
    """

    permission_classes = [IsAuthenticated, HasPermission]
    pagination_class = StandardPagination  # usado também pelo OpenAPI
    service_class = None
    read_serializer_class = None
    write_serializer_class = None

    @property
    def service(self):
        if not hasattr(self, "_service"):
            self._service = self.service_class()
        return self._service

    def get_serializer_context(self):
        return {"request": self.request, "view": self}

    def paginate(self, queryset, request, serializer_class=None):
        serializer_class = serializer_class or self.read_serializer_class
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        data = serializer_class(page, many=True, context=self.get_serializer_context()).data
        return paginator.get_paginated_response(data)

    def respond(self, instance, status_code=status.HTTP_200_OK):
        data = self.read_serializer_class(instance, context=self.get_serializer_context()).data
        return Response(data, status=status_code)


class ListMixin:
    def list(self, request):
        return self.paginate(self.service.list(request.query_params), request)


class CreateMixin:
    def create(self, request):
        serializer = self.write_serializer_class(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        instance = self.service.create(serializer.validated_data, actor=request.user)
        return self.respond(instance, status.HTTP_201_CREATED)


class RetrieveMixin:
    def retrieve(self, request, pk):
        return self.respond(self.service.get(pk))


class UpdateMixin:
    def partial_update(self, request, pk):
        instance = self.service.get(pk)
        serializer = self.write_serializer_class(
            instance, data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        instance = self.service.update(instance, serializer.validated_data, actor=request.user)
        return self.respond(instance)


class DestroyMixin:
    def destroy(self, request, pk):
        self.service.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
