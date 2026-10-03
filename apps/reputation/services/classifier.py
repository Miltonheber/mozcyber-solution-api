import re
from dataclasses import dataclass, field
from typing import Protocol

from django.conf import settings
from django.utils.module_loading import import_string

from apps.reputation.constants import Category, Verdict

FRAUD_THRESHOLD = 0.7
SUSPICIOUS_THRESHOLD = 0.35


@dataclass(frozen=True)
class ClassificationResult:
    verdict: str
    category: str | None
    confidence: float
    explanation: str
    provider: str
    raw: dict = field(default_factory=dict)


class MessageClassifier(Protocol):
    """Contrato de qualquer classificador (regras, IA…). Configurado por `settings.MESSAGE_CLASSIFIER`."""

    def classify(self, number: str, message: str) -> ClassificationResult: ...


# (categoria, regex, peso, motivo)
_RULES = (
    (
        Category.PHISHING,
        r"\b(pin|palavra[- ]passe|password|senha|código de (acesso|verificação))\b",
        0.5,
        "pede credenciais ou códigos",
    ),
    (Category.PHISHING, r"https?://|www\.|\b(bit\.ly|tinyurl)\b", 0.3, "contém ligação suspeita"),
    (Category.FAKE_PRIZE, r"\b(ganhou|premiad[oa]|prémio|sorteio|parabéns)\b", 0.5, "promete prémio"),
    (
        Category.IMPERSONATION,
        r"\b(m-?pesa|e-?mola|m-?kesh|vodacom|movitel|tmcel|banco|bim|standard bank)\b",
        0.2,
        "invoca operador ou banco",
    ),
    (
        Category.IMPERSONATION,
        r"(transferi|enviei|depositei).{0,40}(engano|erro)|devolv[ae]",
        0.5,
        "pede devolução de dinheiro 'enviado por engano'",
    ),
    (
        Category.SIM_SWAP,
        r"(troca|substitui[cç][aã]o|activa[cç][aã]o|ativa[cç][aã]o).{0,20}(sim|chip)|sim swap",
        0.6,
        "refere troca/activação de SIM",
    ),
    (
        Category.LOAN_SCAM,
        r"\b(empr[eé]stimo|cr[eé]dito).{0,60}(taxa|adiantad|pagar)",
        0.6,
        "empréstimo com pagamento antecipado",
    ),
    (
        Category.OTHER,
        r"\b(urgente|imediatamente|conta (bloqueada|suspensa)|últim[oa] aviso)\b",
        0.25,
        "linguagem de urgência/ameaça",
    ),
    # Pedido de pagamento para contas indicadas na mensagem (vários números / titulares de terceiros).
    (
        Category.OTHER,
        r"(mand|envi|transfer|deposit)\w*.{0,60}(conta|e-?mola|m-?pesa|m-?kesh|mpesa)",
        0.25,
        "pede dinheiro para uma conta indicada na mensagem",
    ),
    (
        Category.IMPERSONATION,
        r"em nome d[aeo]|sai nome|vem em nome",
        0.1,
        "indica contas em nome de terceiros",
    ),
    (
        Category.OTHER,
        r"(?s)\b8[2-7]\d{7}\b.{0,200}\b8[2-7]\d{7}\b",
        0.1,
        "indica vários números de conta",
    ),
)


class RuleBasedClassifier:
    """Classificador local por palavras-chave. Serve de default e de fallback até haver um provider de IA."""

    provider = "rule_based"

    def classify(self, number: str, message: str) -> ClassificationResult:
        text = message.lower()
        hits = [(cat, weight, why) for cat, rx, weight, why in _RULES if re.search(rx, text)]
        confidence = round(min(1.0, sum(w for _, w, _ in hits)), 3)
        if confidence >= FRAUD_THRESHOLD:
            verdict = Verdict.FRAUD
        elif confidence >= SUSPICIOUS_THRESHOLD:
            verdict = Verdict.SUSPICIOUS
        else:
            verdict = Verdict.SAFE
        category = self._category(hits) if verdict != Verdict.SAFE else None
        reasons = [why for _, _, why in hits]
        explanation = (
            "Sinais encontrados: " + "; ".join(reasons) + "."
            if reasons
            else "Nenhum sinal de fraude detectado."
        )
        return ClassificationResult(
            verdict=verdict,
            category=category,
            confidence=confidence,
            explanation=explanation,
            provider=self.provider,
            raw={"reasons": reasons},
        )

    @staticmethod
    def _category(hits) -> str:
        totals: dict[str, float] = {}
        for cat, weight, _ in hits:
            totals[cat] = totals.get(cat, 0) + weight
        specific = {c: w for c, w in totals.items() if c != Category.OTHER} or totals
        return max(specific, key=specific.get)


def get_classifier() -> MessageClassifier:
    return import_string(settings.MESSAGE_CLASSIFIER)()
