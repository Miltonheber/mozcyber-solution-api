from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import BaseModel
from apps.reputation.constants import Category, Verdict


class MessageClassification(BaseModel):
    """Histórico de cada análise de mensagem feita pelo classificador."""

    phone_number = models.ForeignKey(
        "reputation.PhoneNumber", on_delete=models.CASCADE, related_name="classifications"
    )
    message = models.TextField()
    verdict = models.CharField(max_length=20, choices=Verdict.choices)
    category = models.CharField(max_length=20, choices=Category.choices, null=True, blank=True)
    confidence = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(1)])
    explanation = models.TextField(blank=True)
    provider = models.CharField(max_length=50)  # ex.: rule_based
    raw_result = models.JSONField(default=dict, blank=True)
    requester_ip = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.phone_number_id} -> {self.verdict}"
