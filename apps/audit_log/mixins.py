import logging

from apps.audit_log.services import LogService

logger = logging.getLogger(__name__)


class LoggingMixin:
    """Regista automaticamente a acção após a resposta. Declare na view:

        log_actions = {"POST": "user.create"}   # método HTTP -> nome da acção
        log_resource_type = "user"

    Falhas ao gravar o log nunca quebram o pedido. Só regista respostas < 500.
    """

    log_actions: dict[str, str] = {}
    log_resource_type: str = ""

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        action = self.log_actions.get(request.method)
        if action and response.status_code < 500:
            try:
                data = response.data if isinstance(getattr(response, "data", None), dict) else {}
                LogService().record(
                    action,
                    user=getattr(request, "user", None),
                    request=request,
                    resource_type=self.log_resource_type,
                    resource_id=self.kwargs.get("pk") or data.get("id", ""),
                    status_code=response.status_code,
                    payload=request.data if hasattr(request, "data") else None,
                )
            except Exception:  # pragma: no cover
                logger.exception("Falha ao registar log de auditoria")
        return response
