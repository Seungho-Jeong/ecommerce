from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class PasswordValidationError(serializers.ValidationError):
    default_detail = _("Password validation error")
    default_code = "password_validation_error"


class InvalidPinError(serializers.ValidationError):
    default_detail = _("Invalid PIN")
    default_code = "invalid_pin"


class TooManyPinAttemptsError(serializers.ValidationError):
    default_detail = _(
        "Too many invalid PIN attempts. Please request a new one."
    )
    default_code = "too_many_pin_attempts"


class ExpiredPinError(serializers.ValidationError):
    default_detail = _("PIN has expired. Please request a new one.")
    default_code = "expired_pin"
