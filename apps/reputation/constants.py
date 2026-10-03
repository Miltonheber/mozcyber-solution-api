from django.db import models


class Category(models.TextChoices):
    PHISHING = "phishing", "Phishing"
    SIM_SWAP = "sim_swap", "SIM swap"
    FAKE_PRIZE = "fake_prize", "Falso prémio"
    IMPERSONATION = "impersonation", "Falsa identidade"
    LOAN_SCAM = "loan_scam", "Falso empréstimo"
    OTHER = "other", "Outro"


class NumberStatus(models.TextChoices):
    UNKNOWN = "unknown", "Desconhecido"
    SUSPICIOUS = "suspicious", "Suspeito"
    BLACKLISTED = "blacklisted", "Blacklist"
    CLEARED = "cleared", "Limpo"


class Verdict(models.TextChoices):
    SAFE = "safe", "Seguro"
    SUSPICIOUS = "suspicious", "Suspeito"
    FRAUD = "fraud", "Fraude"


class ReportStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    CONFIRMED = "confirmed", "Confirmada"
    REJECTED = "rejected", "Rejeitada"


class Channel(models.TextChoices):
    SMS = "sms", "SMS"
    CALL = "call", "Chamada"
    WHATSAPP = "whatsapp", "WhatsApp"
    EMAIL = "email", "Email"
    OTHER = "other", "Outro"


# Reputação: limiares usados por `utils/scoring.py`.
REPORT_WEIGHT = 20
FRAUD_WEIGHT = 25
BLACKLIST_SCORE = 70
BLACKLIST_REPORTS = 3
HIGH_CONFIDENCE = 0.8
