from typing import Any

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import serializers

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
        except ValidationError as exc:
            raise serializers.ValidationError(str(exc))
        return value

    def create(self, validated_data: dict[str, Any]) -> User:
        user = User.objects.create_user(**validated_data)
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
        if not self.instance.check_pin(value):
            self.instance.increase_pin_failures()
            raise serializers.ValidationError("Invalid PIN")
        return value

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.instance.check_pin_attempts():
            raise serializers.ValidationError(
                "Too many invalid PIN attempts. Please request a new one."
            )
        if self.instance.check_pin_expired():
            raise serializers.ValidationError(
                "PIN has expired. Please request a new one."
            )
        return data

    def update(self, instance: User, validated_data: dict[str, Any]) -> User:
        instance.pin = ""
        instance.pin_failures = 0
        instance.pin_sent_at = None
        instance.is_active = True
        instance.save(
            update_fields=["pin", "pin_failures", "pin_sent_at", "is_active"]
        )
        return instance
