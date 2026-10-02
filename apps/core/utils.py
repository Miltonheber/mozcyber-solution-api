SENSITIVE_KEYS = {"password", "old_password", "new_password", "token", "access", "refresh", "secret"}


def redact(data):
    """Substitui valores de chaves sensíveis (recursivo) — usar antes de persistir payloads."""
    if isinstance(data, dict):
        return {k: "***" if str(k).lower() in SENSITIVE_KEYS else redact(v) for k, v in data.items()}
    if isinstance(data, list):
        return [redact(v) for v in data]
    return data
