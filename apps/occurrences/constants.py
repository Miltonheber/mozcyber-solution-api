from django.db import models


class DocumentType(models.TextChoices):
    BI = "bi", "Bilhete de identidade"
    PASSPORT = "passport", "Passaporte"
    DRIVING_LICENSE = "driving_license", "Carta de condução"
    DIRE = "dire", "DIRE"
    OTHER = "other", "Outro"


class OccurrenceStatus(models.TextChoices):
    OPEN = "open", "Aberta"
    FOUND = "found", "Encontrado"
    CLOSED = "closed", "Fechada"
