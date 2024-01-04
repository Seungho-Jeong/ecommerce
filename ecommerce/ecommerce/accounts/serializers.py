from typing import Any

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import serializers

from .exceptions import (
    ExpiredPinError,
    InvalidCredentialsError,
    InvalidPinError,
    NotConfirmedError,
    PasswordValidationError,
    TooManyPinAttemptsError,
)
from .jwt import get_payload, get_user_from_payload
from .models import Address, User


class BaseAccountSerializer(serializers.ModelSerializer):
    """계정 시리얼라이저의 베이스 클래스"""

    class Meta:
        model = User
        fields = ("email", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, value: str) -> str:
        try:
            validate_password(password=value)
        except serializers.ValidationError as e:
            raise PasswordValidationError(e) from e
        return value


class AccountRegisterSerializer(BaseAccountSerializer):
    """계정 등록 시리얼라이저"""

    class Meta:
        model = BaseAccountSerializer.Meta.model
        fields = BaseAccountSerializer.Meta.fields + (
            "username",
            "first_name",
            "last_name",
            "phone_number",
        )
        extra_kwargs = BaseAccountSerializer.Meta.extra_kwargs

    def create(self, validated_data: dict[str, Any]) -> User:
        user = super().create(validated_data)
        user.set_password(validated_data["password"])
        user.save(update_fields=["password"])
        return user


class AccountConfirmationSerializer(BaseAccountSerializer):
    """계정 확인 시리얼라이저"""

    class Meta:
        model = BaseAccountSerializer.Meta.model
        fields = ("email", "pin")
        extra_kwargs = {"pin": {"write_only": True}}

    def validate_pin(self, value: str) -> str:
        """계정생성 시 발급된 PIN이 유효한지 확인한다."""
        if self.instance.check_pin_attempts():
            raise TooManyPinAttemptsError
        if self.instance.check_pin_expired():
            raise ExpiredPinError
        if not self.instance.check_pin(value):
            self.instance.increase_pin_failures()
            raise InvalidPinError
        return value

    def validate_email(self, value: str) -> str:
        """계정이 이미 활성화되었는지 확인한다."""
        if User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError
        return value


class TokenCreateSerializer(BaseAccountSerializer):
    """토큰 생성 시리얼라이저"""

    email = serializers.EmailField()
    password = serializers.CharField()

    def validate_password(self, value: str) -> str:
        return super().validate_password(value)

    def validate_email(self, value: str) -> str:
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise InvalidCredentialsError
        if not user.is_active:
            raise NotConfirmedError
        return value


class TokenRefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(write_only=True)
    user = AccountRegisterSerializer(read_only=True)

    class Meta:
        fields = ("refresh_token", "user")

    def validate_refresh_token(self, value: str) -> str:
        payload = get_payload(value)
        _user = get_user_from_payload(payload)
        return value


class TokenVerifySerializer(serializers.Serializer):
    access_token = serializers.CharField(write_only=True)
    user = AccountRegisterSerializer(read_only=True)

    class Meta:
        fields = ("access_token", "user")

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate_access_token(self, value: str) -> str:
        payload = get_payload(value)
        self.user = get_user_from_payload(payload)
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        validated_data = super().validate(attrs)
        validated_data["user"] = self.user
        return validated_data
