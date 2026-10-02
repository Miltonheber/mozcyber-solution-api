from rest_framework import serializers

from apps.user.models import Permission, Profile


class ProfileMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("id", "code", "name")


class ProfileReadSerializer(serializers.ModelSerializer):
    permissions = serializers.SlugRelatedField(many=True, read_only=True, slug_field="code")

    class Meta:
        model = Profile
        fields = ("id", "code", "name", "description", "permissions", "is_active", "created_at", "updated_at")


class ProfileWriteSerializer(serializers.ModelSerializer):
    permissions = serializers.SlugRelatedField(
        many=True, slug_field="code", queryset=Permission.objects.all(), required=False
    )

    class Meta:
        model = Profile
        fields = ("code", "name", "description", "permissions", "is_active")
