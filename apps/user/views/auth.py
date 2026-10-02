from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.audit_log.mixins import LoggingMixin
from apps.core.views import BaseAPIView
from apps.user.serializers import LoginSerializer, MeSerializer, RefreshSerializer
from apps.user.serializers.auth import AccessSerializer, TokenPairSerializer
from apps.user.services import AuthService


class LoginView(LoggingMixin, BaseAPIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]
    log_actions = {"POST": "auth.login"}
    log_resource_type = "auth"

    @extend_schema(request=LoginSerializer, responses=TokenPairSerializer)
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(AuthService().login(**serializer.validated_data))


class RefreshView(BaseAPIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(request=RefreshSerializer, responses=AccessSerializer)
    def post(self, request, *args, **kwargs):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(AuthService().refresh(serializer.validated_data["refresh"]))


class MeView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=MeSerializer)
    def get(self, request, *args, **kwargs):
        return Response(MeSerializer(request.user, context={"request": request}).data)
