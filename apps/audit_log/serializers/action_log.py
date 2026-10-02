from rest_framework import serializers

from apps.audit_log.models import ActionLog


class ActionLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True, default=None)

    class Meta:
        model = ActionLog
        fields = (
            "id",
            "user",
            "user_email",
            "action",
            "resource_type",
            "resource_id",
            "method",
            "path",
            "status_code",
            "payload",
            "ip_address",
            "user_agent",
            "extra",
            "created_at",
        )
