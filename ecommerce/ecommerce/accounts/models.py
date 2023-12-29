from functools import partial
from typing import Any
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _


class Address(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True)
    street_address_1 = models.CharField(max_length=255)
    street_address_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255)
    city_area = models.CharField(max_length=128, blank=True)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=2)
    country_area = models.CharField(max_length=128, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ("id",)


class User(AbstractUser):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        max_length=150,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
    )
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=30, blank=True)
    addresses = models.ManyToManyField(
        Address, related_name="user_addresses", blank=True
    )
    note = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_password_reset_request = models.DateTimeField(null=True)
    default_shipping_address = models.ForeignKey(
        Address, related_name="+", on_delete=models.SET_NULL, null=True
    )
    default_billing_address = models.ForeignKey(
        Address, related_name="+", on_delete=models.SET_NULL, null=True
    )
    jwt_token_key = models.CharField(
        max_length=12, default=partial(get_random_string, length=12)
    )
    language_code = models.CharField(max_length=35, blank=True)
    search_document = models.TextField(blank=True, default="")
    uuid = models.UUIDField(default=uuid4, unique=True)
    pin = models.CharField(max_length=settings.PIN_MAX_LENGTH, blank=True)
    pin_failures = models.PositiveSmallIntegerField(default=0)
    pin_sent_at = models.DateTimeField(null=True)
    is_active = models.BooleanField(
        _("active"),
        default=False,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ("email",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return str(self.email)

    def check_pin(self, pin: str) -> bool:
        """사용자가 제공한 PIN이 올바른지 확인합니다."""
        return self.pin == pin

    def check_pin_attempts(self) -> bool:
        """사용자가 PIN을 입력할 수 있는지 확인합니다."""
        return self.pin_failures >= settings.PIN_FAILURES_LIMIT

    def check_pin_expired(self) -> bool:
        """사용자의 PIN이 만료되었는지 확인합니다."""

        def _is_expired_pin(self) -> bool:
            return timezone.now() > self.pin_sent_at + timezone.timedelta(
                seconds=settings.PIN_EXPIRE_TIMEDELTA_SECONDS
            )

        return self.pin_sent_at is None or _is_expired_pin(self)

    def increase_pin_failures(self) -> None:
        """사용자의 PIN 실패 횟수를 증가시킵니다."""
        self.pin_failures += 1
        self.save(update_fields=["pin_failures"])
