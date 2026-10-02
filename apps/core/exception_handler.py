from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .exceptions import BusinessException

_CODES = {
    drf_exceptions.ValidationError: "validation_error",
    drf_exceptions.NotAuthenticated: "unauthorized",
    drf_exceptions.AuthenticationFailed: "unauthorized",
    drf_exceptions.PermissionDenied: "permission_denied",
    drf_exceptions.NotFound: "not_found",
    drf_exceptions.MethodNotAllowed: "method_not_allowed",
}


def error_body(code: str, message: str, details=None) -> dict:
    return {"code": code, "message": message, "details": details}


def api_exception_handler(exc, context):
    """Formato único de erro: {code, message, details}."""
    if isinstance(exc, BusinessException):
        return Response(error_body(exc.code, exc.message, exc.details), status=exc.status_code)

    if isinstance(exc, DjangoValidationError):
        exc = drf_exceptions.ValidationError(exc.messages)

    response = exception_handler(exc, context)
    if response is None:
        return None  # erro inesperado -> 500 do Django

    if isinstance(exc, drf_exceptions.ValidationError):
        message, details = "Dados inválidos.", response.data
    else:
        detail = getattr(exc, "detail", None)
        message = str(detail.get("detail", detail)) if isinstance(detail, dict) else str(detail)
        details = None
    code = next(
        (c for cls, c in _CODES.items() if isinstance(exc, cls)), getattr(exc, "default_code", "error")
    )
    response.data = error_body(code, message, details)
    return response
