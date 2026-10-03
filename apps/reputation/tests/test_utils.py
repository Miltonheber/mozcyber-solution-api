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
        (dict(reports=3, frauds=0, current_status=U), (70, B)),  # blacklist => score mínimo
        (dict(reports=0, frauds=1, current_status=U, high_confidence_fraud=True), (70, B)),
        (dict(reports=0, frauds=1, current_status=U), (25, S)),
        (dict(reports=0, frauds=0, current_status=B), (70, B)),  # nunca baixa sozinho
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


PAYMENT_REDIRECT = (
    "O Dinheiro Podes Mandar Nesta Conta Na E-mola 871937243 Vem Em Nome De Tomas Augusto Moises "
    "Ou 840713788 Sai Nome De Adelina Mateus Zacarias"
)


def test_rule_based_flags_payment_redirect_to_third_party_accounts():
    result = RuleBasedClassifier().classify("+258841234567", PAYMENT_REDIRECT)
    assert result.verdict == "suspicious" and result.category is not None
    assert any("conta" in r for r in result.raw["reasons"])


@pytest.mark.parametrize(
    "text",
    ["Bom dia, vamos almoçar amanhã?", "A sua reunião é às 10h na sala 2.", "Obrigado pela ajuda ontem."],
)
def test_rule_based_payment_rules_do_not_flag_normal_chat(text):
    assert RuleBasedClassifier().classify("+258841234567", text).verdict == "safe"
