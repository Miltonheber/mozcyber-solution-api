from apps.core.services import BaseService
from apps.reputation.constants import HIGH_CONFIDENCE, Verdict
from apps.reputation.repositories import MessageClassificationRepository
from apps.reputation.services.classifier import get_classifier
from apps.reputation.services.phone_number_service import PhoneNumberService


class ClassificationService(BaseService):
    repository_class = MessageClassificationRepository

    def __init__(self, repository=None, phones=None, classifier=None):
        super().__init__(repository)
        self.phones = phones or PhoneNumberService()
        self.classifier = classifier or get_classifier()

    def classify(self, number: str, message: str, ip: str | None = None) -> dict:
        """Classifica a mensagem, guarda o histórico e alimenta a reputação do número."""
        result = self.classifier.classify(number, message)
        phone = self.phones.repository.get_or_create_by_number(number)
        self.repository.create(
            phone_number=phone,
            message=message,
            verdict=result.verdict,
            category=result.category,
            confidence=result.confidence,
            explanation=result.explanation,
            provider=result.provider,
            raw_result=result.raw,
            requester_ip=ip,
        )
        phone = self.phones.register_activity(
            number,
            category=result.category if result.verdict != Verdict.SAFE else None,
            high_confidence_fraud=result.verdict == Verdict.FRAUD and result.confidence >= HIGH_CONFIDENCE,
        )
        return {
            "verdict": result.verdict,
            "category": result.category,
            "confidence": result.confidence,
            "explanation": result.explanation,
            "reputation": phone,
        }
