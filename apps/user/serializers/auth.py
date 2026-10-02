from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class TokenPairSerializer(serializers.Serializer):  # apenas para documentação (Swagger)
    access = serializers.CharField()
    refresh = serializers.CharField()


class AccessSerializer(serializers.Serializer):  # apenas para documentação (Swagger)
    access = serializers.CharField()
