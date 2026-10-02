from rest_framework import serializers

from apps.user.models import Permission


class PermissionReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ("id", "code", "name", "description", "is_active", "created_at", "updated_at")


class PermissionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ("code", "name", "description", "is_active")
