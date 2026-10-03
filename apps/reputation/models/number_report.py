from django.db import models

from apps.core.models import BaseModel
from apps.reputation.constants import Category, Channel, ReportStatus


class NumberReport(BaseModel):
    """Denúncia pública de um número / tentativa de burla (anónima: `created_by` fica nulo)."""

    phone_number = models.ForeignKey(
        "reputation.PhoneNumber", on_delete=models.CASCADE, related_name="reports"
    )
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    behavior = models.TextField()
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.OTHER)
    amount_lost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    reporter_contact = models.CharField(max_length=100, blank=True)
    reporter_ip = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ReportStatus.choices, default=ReportStatus.PENDING)
    moderation_note = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"{self.phone_number_id} ({self.category}, {self.status})"
