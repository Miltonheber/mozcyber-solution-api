import pytest

from apps.reputation.constants import NumberStatus
from apps.reputation.services.classifier import RuleBasedClassifier
from apps.reputation.utils.scoring import compute_reputation

U, S, B = NumberStatus.UNKNOWN, NumberStatus.SUSPICIOUS, NumberStatus.BLACKLISTED


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        (dict(reports=0, frauds=0, current_status=U), (0, U)),
        (dict(reports=1, frauds=0, current_status=U), (20, S)),
        (dict(reports=3, frauds=0, current_status=U), (60, B)),
        (dict(reports=0, frauds=1, current_status=U, high_confidence_fraud=True), (25, B)),
        (dict(reports=0, frauds=1, current_status=U), (25, S)),
        (dict(reports=0, frauds=0, current_status=B), (0, B)),  # nunca baixa sozinho
        (dict(reports=10, frauds=10, current_status=U), (100, B)),
    ],
)
def test_compute_reputation(kwargs, expected):
    assert compute_reputation(**kwargs) == expected


def test_rule_based_flags_fraud_and_safe():
    clf = RuleBasedClassifier()
    fraud = clf.classify("+258841234567", "Parabéns, ganhou um prémio! Envie o seu PIN M-Pesa em http://x.co")
    assert fraud.verdict == "fraud" and fraud.confidence >= 0.8 and fraud.category
    safe = clf.classify("+258841234567", "Olá, vamos almoçar amanhã?")
    assert safe.verdict == "safe" and safe.category is None and safe.confidence == 0
