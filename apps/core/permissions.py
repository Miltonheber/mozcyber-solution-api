from rest_framework.permissions import BasePermission

PERMISSIONS_CLAIM = "permissions"
PROFILES_CLAIM = "profiles"


def require_permissions(*codes: str):
    """Decorador para métodos HTTP de uma view: exige TODAS as permissões `codes` (claim do JWT).

        @require_permissions("user:read")
        def get(self, request, *args, **kwargs): ...

    Método sem decorador => basta estar autenticado.
    """

    def decorator(handler):
        handler.required_permissions = tuple(codes)
        return handler

    return decorator


class HasPermission(BasePermission):
    """Lê as permissões declaradas por `@require_permissions` no handler do método HTTP e valida-as
    contra a claim `permissions` do token, sem ir à BD."""

    message = "Sem permissão para esta acção."

    def has_permission(self, request, view):
        handler = getattr(view, request.method.lower(), None)
        required = getattr(handler, "required_permissions", None)
        if not required:
            return True
        token = request.auth
        granted = set(token.get(PERMISSIONS_CLAIM, [])) if token is not None else set()
        return set(required) <= granted
