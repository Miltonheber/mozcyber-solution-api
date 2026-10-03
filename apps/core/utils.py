SENSITIVE_KEYS = {
    "password",
    "old_password",
    "new_password",
    "token",
    "access",
    "refresh",
    "secret",
    # dados pessoais (ocorrências, denúncias)
    "document_number",
    "owner_contact",
    "reporter_contact",
}


def redact(data):
    """Substitui valores de chaves sensíveis (recursivo) — usar antes de persistir payloads."""
    if isinstance(data, dict):
        return {k: "***" if str(k).lower() in SENSITIVE_KEYS else redact(v) for k, v in data.items()}
    if isinstance(data, list):
        return [redact(v) for v in data]
    return data


def normalize_phone(raw: str, default_country_code: str = "258") -> str:
    """Normaliza um número para E.164 (`+258841234567`). Levanta `ValueError` se inválido.

    Aceita espaços, hífens, parênteses, prefixo `+` ou `00`; números locais de 9 dígitos
    recebem `default_country_code`.
    """
    digits = "".join(ch for ch in str(raw) if ch.isdigit())
    if str(raw).strip().startswith("00"):
        digits = digits[2:]
    elif len(digits) == 9:
        digits = default_country_code + digits
    if not 8 <= len(digits) <= 15:
        raise ValueError("Número de telefone inválido.")
    return f"+{digits}"
