from rest_framework import serializers

from apps.reputation.models import NumberReport

from .phone_number import PhoneField


class PublicReportCreateSerializer(serializers.ModelSerializer):
    phone = PhoneField(max_length=30)

    class Meta:
        model = NumberReport
        fields = ("phone", "category", "behavior", "channel", "amount_lost", "reporter_contact")
        extra_kwargs = {"behavior": {"max_length": 2000}}


class PublicReportReadSerializer(serializers.ModelSerializer):
    number = serializers.CharField(source="phone_number.number", read_only=True)

    class Meta:
        model = NumberReport
        fields = ("id", "number", "category", "status", "created_at")
        read_only_fields = fields


class NumberReportReadSerializer(serializers.ModelSerializer):
    number = serializers.CharField(source="phone_number.number", read_only=True)

    class Meta:
        model = NumberReport
        fields = (
            "id",
            "number",
            "category",
            "behavior",
            "channel",
            "amount_lost",
            "reporter_contact",
            "reporter_ip",
            "status",
            "moderation_note",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class NumberReportModerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NumberReport
        fields = ("status", "moderation_note")
