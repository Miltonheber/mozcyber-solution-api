from django.db import models

from apps.core.models import BaseModel


class Profile(BaseModel):
    code = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField("user.Permission", related_name="profiles", blank=True)

    class Meta(BaseModel.Meta):
        ordering = ("code",)

    def __str__(self):
        return self.code
