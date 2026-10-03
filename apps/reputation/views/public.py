from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response

from apps.audit_log.mixins import LoggingMixin
from apps.audit_log.utils.request import get_client_ip
from apps.core.exceptions import ValidationException
from apps.core.utils import normalize_phone
from apps.core.views import PublicAPIView
from apps.reputation.serializers import (
    ClassifyRequestSerializer,
    ClassifyResponseSerializer,
    PublicReportCreateSerializer,
    PublicReportReadSerializer,
    PublicReputationSerializer,
)
from apps.reputation.services import ClassificationService, PhoneNumberService, ReportService


class PublicClassifyView(LoggingMixin, PublicAPIView):
    """Classifica (número, mensagem) e alimenta a reputação do número."""

    throttle_scope = "public_classify"
    service_class = ClassificationService
    log_actions = {"POST": "reputation.classify"}
    log_resource_type = "classification"

    @extend_schema(request=ClassifyRequestSerializer, responses=ClassifyResponseSerializer)
    def post(self, request, *args, **kwargs):
        serializer = ClassifyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = self.service.classify(
            serializer.validated_data["phone"],
            serializer.validated_data["message"],
            ip=get_client_ip(request),
        )
        return Response(ClassifyResponseSerializer(result).data)


class PublicReportView(LoggingMixin, PublicAPIView):
    """Denúncia de um número / tentativa de burla."""

    throttle_scope = "public_report"
    service_class = ReportService
    log_actions = {"POST": "reputation.report"}
    log_resource_type = "report"

    @extend_schema(request=PublicReportCreateSerializer, responses={201: PublicReportReadSerializer})
    def post(self, request, *args, **kwargs):
        serializer = PublicReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        number = data.pop("phone")
        report = self.service.report(number, data, ip=get_client_ip(request), actor=self.get_actor(request))
        return Response(PublicReportReadSerializer(report).data, status=status.HTTP_201_CREATED)


class PublicNumberReputationView(PublicAPIView):
    """Reputação de um número. Número nunca visto => `status: unknown` (não é erro)."""

    throttle_scope = "public_read"
    service_class = PhoneNumberService

    @extend_schema(responses=PublicReputationSerializer)
    def get(self, request, phone, *args, **kwargs):
        try:
            number = normalize_phone(phone)
        except ValueError as exc:
            raise ValidationException(str(exc)) from None
        return Response(PublicReputationSerializer(self.service.reputation(number)).data)
