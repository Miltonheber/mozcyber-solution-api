from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions import UnauthorizedException
from apps.user.repositories import UserRepository
from apps.user.utils.tokens import build_tokens


class AuthService:
    def __init__(self, user_repository: UserRepository | None = None):
        self.users = user_repository or UserRepository()

    def login(self, email: str, password: str) -> dict:
        user = authenticate(username=email, password=password)
        if user is None:
            raise UnauthorizedException("Credenciais inválidas.", code="invalid_credentials")
        update_last_login(None, user)
        return build_tokens(user)

    def refresh(self, refresh_token: str) -> dict:
        """Emite novo access com claims recalculadas (permissões actuais da BD)."""
        try:
            payload = RefreshToken(refresh_token)
        except TokenError:
            raise UnauthorizedException("Token inválido ou expirado.", code="invalid_token") from None
        user = self.users.get_active_by_id(payload[api_settings.USER_ID_CLAIM])
        if user is None:
            raise UnauthorizedException("Utilizador inválido.", code="invalid_token") from None
        return {"access": build_tokens(user)["access"]}
