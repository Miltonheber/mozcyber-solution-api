import datetime

from rest_framework import serializers

from apps.occurrences.constants import OccurrenceStatus
from apps.occurrences.models import LostDocumentOccurrence


class OccurrenceReadSerializer(serializers.ModelSerializer):
    registered_by = serializers.SerializerMethodField()

    class Meta:
        model = LostDocumentOccurrence
        fields = (
            "id",
            "reference",
            "document_type",
            "document_number",
            "owner_name",
            "owner_contact",
            "lost_at",
            "location",
            "description",
            "status",
            "station_name",
            "registered_by",
            "closed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_registered_by(self, obj) -> str | None:
        user = obj.created_by  # pré-carregado pelo repository
        return (user.name or user.email) if user else None


class OccurrenceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LostDocumentOccurrence
        fields = (
            "document_type",
            "document_number",
            "owner_name",
            "owner_contact",
            "lost_at",
            "location",
            "description",
            "station_name",
            "status",
        )

    def validate_document_number(self, value):
        value = value.strip().upper()
        if not value:
            raise serializers.ValidationError("Indique o número do documento.")
        return value

    def validate_lost_at(self, value):
        if value > datetime.date.today():
            raise serializers.ValidationError("A data da perda não pode ser futura.")
        return value

    def validate_status(self, value):
        if self.instance is None and value != OccurrenceStatus.OPEN:
            raise serializers.ValidationError("Uma ocorrência nova começa sempre aberta.")
        return value
