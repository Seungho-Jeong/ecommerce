from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers, status


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


class InvalidCredentialsError(exceptions.AuthenticationFailed):
    default_detail = _("Invalid credentials")
    default_code = "invalid_credentials"
    status_code = status.HTTP_401_UNAUTHORIZED


class JWTTokenSignatureExpiredError(exceptions.AuthenticationFailed):
    default_detail = _("Signature has expired")
    default_code = "signature_has_expired"
    status_code = status.HTTP_401_UNAUTHORIZED


class JWTDecodeError(exceptions.AuthenticationFailed):
    default_detail = _("Error decoding signature")
    default_code = "error_decoding_signature"
    status_code = status.HTTP_401_UNAUTHORIZED


class JWTInvalidTokenError(exceptions.AuthenticationFailed):
    default_detail = _("Invalid token")
    default_code = "invalid_token"
    status_code = status.HTTP_401_UNAUTHORIZED


class NotConfirmedError(exceptions.AuthenticationFailed):
    default_detail = _("Account has not been confirmed")
    default_code = "not_confirmed"
    status_code = status.HTTP_401_UNAUTHORIZED


class DoesNotExistUserError(exceptions.AuthenticationFailed):
    default_detail = _("User does not exist")
    default_code = "does_not_exist_user"
    status_code = status.HTTP_401_UNAUTHORIZED
