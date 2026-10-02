from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.core.permissions import PERMISSIONS_CLAIM, PROFILES_CLAIM
from apps.user.models import Profile, User

from .profile import ProfileMiniSerializer


class UserReadSerializer(serializers.ModelSerializer):
    profiles = ProfileMiniSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "name", "profiles", "is_active", "last_login", "created_at", "updated_at")


class UserWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    profiles = serializers.SlugRelatedField(
        many=True, slug_field="code", queryset=Profile.objects.all(), required=False
    )

    class Meta:
        model = User
        fields = ("email", "name", "password", "profiles", "is_active")

    def validate_password(self, value):
        validate_password(value)
        return value


class MeSerializer(UserReadSerializer):
    """Utilizador autenticado + perfis/permissões lidos das claims do token (sem queries extra)."""

    claims = serializers.SerializerMethodField()

    class Meta(UserReadSerializer.Meta):
        fields = UserReadSerializer.Meta.fields + ("claims",)

    def get_claims(self, obj) -> dict:
        token = self.context["request"].auth
        return {
            PROFILES_CLAIM: token.get(PROFILES_CLAIM, []),
            PERMISSIONS_CLAIM: token.get(PERMISSIONS_CLAIM, []),
        }
