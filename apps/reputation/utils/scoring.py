from apps.reputation.constants import (
    BLACKLIST_REPORTS,
    BLACKLIST_SCORE,
    FRAUD_WEIGHT,
    REPORT_WEIGHT,
    NumberStatus,
)


def compute_reputation(
    *, reports: int, frauds: int, current_status: str, high_confidence_fraud: bool = False
) -> tuple[int, str]:
    """(risk_score, status) a partir dos contadores. Nunca baixa um número da blacklist (só a moderação)."""
    score = min(100, reports * REPORT_WEIGHT + frauds * FRAUD_WEIGHT)
    if current_status == NumberStatus.BLACKLISTED:
        return score, NumberStatus.BLACKLISTED
    if reports >= BLACKLIST_REPORTS or high_confidence_fraud or score >= BLACKLIST_SCORE:
        return score, NumberStatus.BLACKLISTED
    if score > 0:
        return score, NumberStatus.SUSPICIOUS
    return score, current_status
