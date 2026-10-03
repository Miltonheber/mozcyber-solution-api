from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel
from apps.reputation.constants import Category, NumberStatus


class PhoneNumber(BaseModel):
    """Reputação de um número (E.164). Um registo por número; é a blacklist do sistema."""

    number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=NumberStatus.choices, default=NumberStatus.UNKNOWN)
    category = models.CharField(max_length=20, choices=Category.choices, null=True, blank=True)
    risk_score = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)])
    report_count = models.PositiveIntegerField(default=0)
    classification_count = models.PositiveIntegerField(default=0)
    fraud_count = models.PositiveIntegerField(default=0)
    first_seen_at = models.DateTimeField(default=timezone.now)
    last_reported_at = models.DateTimeField(null=True, blank=True)
    blacklisted_at = models.DateTimeField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        indexes = [
            models.Index(fields=["status", "category"]),
        ]

    def __str__(self):
        return f"{self.number} ({self.status})"
