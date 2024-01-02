from typing import Any

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import serializers

from .exceptions import (
    ExpiredPinError,
    InvalidPinError,
    PasswordValidationError,
    TooManyPinAttemptsError,
)
from .models import Address, User


class AccountRegisterSerializer(serializers.ModelSerializer):
    """계정 등록 시리얼라이저"""

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "username",
            "first_name",
            "last_name",
            "phone_number",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, value: str) -> str:
        try:
            validate_password(password=value)
        except serializers.ValidationError as e:
            raise PasswordValidationError(e) from e
        return value

    def create(self, validated_data: dict[str, Any]) -> User:
        user = super().create(validated_data)
        user.set_password(validated_data["password"])
        user.save(update_fields=["password"])
        return user

    def generate_pin(self) -> str:
        pin = get_random_string(
            length=settings.PIN_MAX_LENGTH, allowed_chars="0123456789"
        )
        self.instance.pin = pin
        self.instance.pin_sent_at = timezone.now()
        self.instance.save(update_fields=["pin", "pin_sent_at"])
        return pin


class AccountConfirmationSerializer(serializers.ModelSerializer):
    """계정 확인 시리얼라이저"""

    class Meta:
        model = User
        fields = ("email", "pin")

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
