from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Address, User

UserModel = get_user_model()


class AccountRegisterSerializer(serializers.ModelSerializer):
    """Account register serializer."""

    class Meta:
        """Meta class."""

        model = UserModel
        fields = ("email", "password", "username")
        extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, value: str) -> str:
        """Validate password."""
        try:
            validate_password(password=value)
        except ValidationError as exc:
            raise serializers.ValidationError(str(exc))
        return value

    def create(self, validated_data: dict[str, Any]) -> UserModel:
        """Create user."""
        user = UserModel.objects.create_user(**validated_data)
        return user
