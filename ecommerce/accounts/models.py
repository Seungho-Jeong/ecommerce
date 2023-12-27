from functools import partial
from typing import Any
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string


class Address(models.Model):
    """Address model."""

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
    """Custom user model."""

    email = models.EmailField(unique=True)
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

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ("email",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return str(self.uuid)
