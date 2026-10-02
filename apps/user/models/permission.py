from django.db import models

from apps.core.models import BaseModel


class Permission(BaseModel):
    code = models.CharField(max_length=100, unique=True)  # ex.: user:read
    name = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)

    class Meta(BaseModel.Meta):
        ordering = ("code",)

    def __str__(self):
        return self.code
