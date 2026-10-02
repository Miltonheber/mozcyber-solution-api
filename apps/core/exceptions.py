"""Exceções de negócio partilhadas. Services levantam estas; o exception handler converte em HTTP."""


class BusinessException(Exception):
    status_code = 400
    code = "business_error"
    message = "Erro de negócio."

    def __init__(self, message: str | None = None, *, code: str | None = None, details=None):
        self.message = message or self.message
        self.code = code or self.code
        self.details = details
        super().__init__(self.message)


class ValidationException(BusinessException):
    status_code = 400
    code = "validation_error"
    message = "Dados inválidos."


class UnauthorizedException(BusinessException):
    status_code = 401
    code = "unauthorized"
    message = "Não autenticado."


class PermissionDeniedException(BusinessException):
    status_code = 403
    code = "permission_denied"
    message = "Sem permissão para esta acção."


class NotFoundException(BusinessException):
    status_code = 404
    code = "not_found"
    message = "Recurso não encontrado."


class ConflictException(BusinessException):
    status_code = 409
    code = "conflict"
    message = "Conflito com o estado actual do recurso."
