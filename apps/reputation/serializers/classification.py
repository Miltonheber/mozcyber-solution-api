from rest_framework import serializers

from apps.reputation.constants import Category, Verdict

from .phone_number import PhoneField, PublicReputationSerializer


class ClassifyRequestSerializer(serializers.Serializer):
    phone = PhoneField(max_length=30)
    message = serializers.CharField(max_length=2000, trim_whitespace=True)


class ClassifyResponseSerializer(serializers.Serializer):
    verdict = serializers.ChoiceField(choices=Verdict.choices)
    category = serializers.ChoiceField(choices=Category.choices, allow_null=True)
    confidence = serializers.FloatField()
    explanation = serializers.CharField()
    reputation = PublicReputationSerializer()
