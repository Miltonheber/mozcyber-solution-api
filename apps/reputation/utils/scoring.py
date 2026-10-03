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
    blacklisted = (
        current_status == NumberStatus.BLACKLISTED
        or reports >= BLACKLIST_REPORTS
        or high_confidence_fraud
        or score >= BLACKLIST_SCORE
    )
    if blacklisted:
        return max(score, BLACKLIST_SCORE), NumberStatus.BLACKLISTED
    if score > 0:
        return score, NumberStatus.SUSPICIOUS
    return score, current_status
