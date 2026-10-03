from django.db import models


class Topic(models.TextChoices):
    SCAMS = "scams", "Burlas"
    SOCIAL_ENGINEERING = "social_engineering", "Engenharia social"
    CREDENTIALS = "credentials", "Protecção de credenciais"
    SIM_SWAP = "sim_swap", "SIM swap"


class PostStatus(models.TextChoices):
    DRAFT = "draft", "Rascunho"
    PUBLISHED = "published", "Publicado"
