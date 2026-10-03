from rest_framework import serializers

from apps.core.utils import normalize_phone
from apps.reputation.models import PhoneNumber


class PhoneField(serializers.CharField):
    """Telefone livre -> E.164 normalizado."""

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        try:
            return normalize_phone(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from None


class PublicReputationSerializer(serializers.ModelSerializer):
    """Reputação exposta publicamente: só o mínimo."""

    class Meta:
        model = PhoneNumber
        fields = ("number", "status", "category", "risk_score", "report_count")
        read_only_fields = fields


class PublicHallOfFameSerializer(PublicReputationSerializer):
    """Item do ranking público: reputação mínima + data de entrada na blacklist."""

    class Meta(PublicReputationSerializer.Meta):
        fields = (*PublicReputationSerializer.Meta.fields, "blacklisted_at")
        read_only_fields = fields


class PhoneNumberReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = (
            "id",
            "number",
            "status",
            "category",
            "risk_score",
            "report_count",
            "classification_count",
            "fraud_count",
            "first_seen_at",
            "last_reported_at",
            "blacklisted_at",
            "updated_at",
        )
        read_only_fields = fields


class PhoneNumberModerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = ("status", "category")
