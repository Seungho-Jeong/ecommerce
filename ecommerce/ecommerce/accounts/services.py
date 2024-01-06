from typing import Any

from django.conf import settings

from . import emails
from .exceptions import InvalidCredentialsError
from .jwt import (
    create_access_token,
    create_refresh_token,
    get_payload,
    get_user_from_payload,
)
from .models import User


class AccountService:
    def __init__(self, serializer, request=None):
        self.serializer = serializer
        self.request = request

    def create_user(self) -> User:
        """사용자를 생성하고 이메일 인증이 활성화되어 있으면 이메일을 보냅니다."""
        instance = self.serializer.save()
        if settings.ENABLE_CONFIRMATION_BY_EMAIL:
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
            settings.JWT_ACCESS_TYPE: access_token,
            settings.JWT_REFRESH_TYPE: refresh_token,
        }

    def verify_token(self) -> User:
        """토큰을 확인하고 사용자를 반환합니다."""
        token = self.request.META.get("HTTP_AUTHORIZATION")
        if not token:
            raise InvalidCredentialsError
        payload = get_payload(token)
        user = get_user_from_payload(payload)
        return user
