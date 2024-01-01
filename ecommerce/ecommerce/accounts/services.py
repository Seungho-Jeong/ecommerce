from typing import Any

from django.conf import settings
from django.middleware.csrf import _get_new_csrf_string
from django.utils.crypto import get_random_string

from . import emails
from .exceptions import InvalidCredentialsError
from .jwt import create_access_token, create_refresh_token
from .models import User


class AccountService:
    def __init__(self, serializer, request=None):
        self.serializer = serializer
        self.request = request

    def create_user(self) -> User:
        """사용자를 생성하고 이메일 인증이 활성화되어 있으면 이메일을 보냅니다."""
        instance = self.serializer.save()
        if settings.ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL:
            pin = instance.set_pin()
            emails.send_account_confirmation_email(instance, pin)
        else:
            instance.activate()
        return instance

    def _retrieve_user_from_credentials(self, email, password) -> User | None:
        """이메일과 비밀번호를 사용하여 사용자를 검색합니다."""
        user = User.objects.filter(email=email, is_active=True).first()
        if user and user.check_password(password):
            return user
        return None

    def get_user(self) -> User:
        """이메일과 비밀번호를 사용하여 사용자를 검색합니다."""
        email = self.serializer.validated_data["email"]
        password = self.serializer.validated_data["password"]

        user = self._retrieve_user_from_credentials(email, password)
        if not user:
            raise InvalidCredentialsError
        return user

    def create_tokens(self, user: User) -> dict[str, Any]:
        """사용자에게 토큰을 발급합니다."""
        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "csrf": _get_new_csrf_string(),
        }
