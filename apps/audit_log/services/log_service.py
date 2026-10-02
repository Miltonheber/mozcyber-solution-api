from apps.audit_log.repositories import ActionLogRepository
from apps.audit_log.utils.request import get_client_ip, get_user_agent
from apps.core.services import BaseService
from apps.core.utils import redact


class LogService(BaseService):
    repository_class = ActionLogRepository

    def record(
        self,
        action: str,
        *,
        user=None,
        request=None,
        resource_type: str = "",
        resource_id="",
        status_code: int | None = None,
        payload=None,
        extra=None,
    ):
        """Regista uma acção. Se `request` for dado, extrai method/path/ip/user-agent automaticamente."""
        data = {
            "action": action,
            "user": user if user is not None and getattr(user, "is_authenticated", False) else None,
            "resource_type": resource_type,
            "resource_id": str(resource_id or ""),
            "status_code": status_code,
            "payload": redact(payload) if payload else {},
            "extra": extra or {},
        }
        if request is not None:
            data.update(
                method=request.method,
                path=request.get_full_path()[:500],
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
            )
        return self.repository.create(**data)
