from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.test import APIClient, APITestCase, override_settings

from ..exceptions import (
    ExpiredPinError,
    InvalidCredentialsError,
    InvalidPinError,
    PasswordValidationError,
    TooManyPinAttemptsError,
)
from ..models import User
from ..serializers import (
    AccountConfirmationSerializer,
    AccountRegisterSerializer,
    TokenCreateSerializer,
    TokenVerifySerializer,
)


class AccountRegisterTestCase(APITestCase):
    """계정 등록 테스트"""

    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()
        self.url = reverse("signup")
        self.model = User
        self.serializer = AccountRegisterSerializer
        self.data = {
            "email": "test@test.com",
            "password": "test1234!!",
            "username": "test_user",
        }

    def test_serializer(self):
        serializer = self.serializer(data=self.data)
        self.assertTrue(serializer.is_valid())

    def test_validate_email(self):
        serializer = self.serializer(data=self.data)
        self.assertTrue(serializer.is_valid())

        self.data["email"] = "invalid_mail_format.com"
        serializer = self.serializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertRaises(serializers.ValidationError)

    def test_validate_password(self):
        serializer = self.serializer(data=self.data)
        self.assertTrue(serializer.is_valid())

        self.data["password"] = "short"
        serializer = self.serializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertRaises(PasswordValidationError)

    def test_create(self):
        serializer = self.serializer(data=self.data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(user.email, self.data["email"])
        self.assertTrue(user.check_password(self.data["password"]))
        self.assertEqual(user.username, self.data["username"])

    @override_settings(
        ENABLE_CONFIRMATION_BY_EMAIL=True,
        ALLOWED_CLIENT_HOSTS=["localhost"],
    )
    @patch("ecommerce.accounts.emails._send_account_confirmation_email")
    def test_register_account(self, send_account_confirmation_email_mock):
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            send_account_confirmation_email_mock.delay.call_count, 1
        )

        self.assertEqual(self.model.objects.count(), 1)
        self.assertEqual(self.model.objects.get().email, self.data["email"])
        self.assertEqual(
            self.model.objects.get().username, self.data["username"]
        )
        self.assertTrue(
            self.model.objects.get().check_password(self.data["password"])
        )
        self.assertEqual(self.model.objects.get().is_active, False)
        self.assertEqual(self.model.objects.get().is_staff, False)
        self.assertEqual(self.model.objects.get().is_superuser, False)
        self.assertEqual(self.model.objects.get().groups.count(), 0)
        self.assertEqual(self.model.objects.get().user_permissions.count(), 0)


class AccountConfirmationViewTestCase(APITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()
        self.url = reverse("confirm")
        self.model = User
        self.serializer = AccountConfirmationSerializer

        self.pin = "123456"
        self.user = self.model.objects.create_user(
            email="test@test.com",
            password="test1234!!",
            username="test_user",
            pin=self.pin,
            pin_sent_at=timezone.now(),
        )
        self.data = {
            "email": self.user.email,
            "pin": self.pin,
        }

    def test_serializer(self):
        serializer = self.serializer(instance=self.user, data=self.data)
        self.assertTrue(serializer.is_valid())

    def test_validate_pin(self):
        serializer = self.serializer(instance=self.user, data=self.data)
        self.assertTrue(serializer.is_valid())

        self.data["pin"] = "000000"
        serializer = self.serializer(instance=self.user, data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertRaises(InvalidPinError)

    @override_settings(PIN_EXPIRE_TIMEDELTA_SECONDS=60)
    def test_validate_pin_expired(self):
        serializer = self.serializer(instance=self.user, data=self.data)
        self.assertTrue(serializer.is_valid())

        self.user.pin_sent_at = timezone.now() - timezone.timedelta(seconds=60)
        self.user.save()
        serializer = self.serializer(instance=self.user, data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertRaises(ExpiredPinError)

    @override_settings(PIN_FAILURES_LIMIT=5)
    def test_validate_pin_failures_limit(self):
        serializer = self.serializer(instance=self.user, data=self.data)
        self.assertTrue(serializer.is_valid())

        self.user.pin_failures = 5
        self.user.save()
        serializer = self.serializer(instance=self.user, data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertRaises(TooManyPinAttemptsError)

    def test_confirm_account(self):
        self.assertEqual(self.user.is_active, False)
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.is_active, True)
        self.assertEqual(self.user.pin, "")
        self.assertEqual(self.user.pin_sent_at, None)
        self.assertEqual(self.user.pin_failures, 0)


class TokenCreateViewTestCase(APITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()
        self.url = reverse("signin")
        self.model = User
        self.serializer = TokenCreateSerializer

        self.user = self.model.objects.create_user(
            email="test@test.com",
            password="test1234!!",
            username="test_user",
            is_active=True,
        )
        self.data = {
            "email": self.user.email,
            "password": "test1234!!",
        }

    def test_serializer(self):
        serializer = self.serializer(data=self.data)
        self.assertTrue(serializer.is_valid())

    def test_validate_email(self):
        serializer = self.serializer(data=self.data)
        self.assertTrue(serializer.is_valid())

        self.data["email"] = "invalid_mail_format.com"
        serializer = self.serializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertRaises(serializers.ValidationError)

    def test_validate_password(self):
        serializer = self.serializer(data=self.data)
        self.assertTrue(serializer.is_valid())

        self.data["password"] = "short"
        serializer = self.serializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertRaises(PasswordValidationError)

    def test_invalid_credentials(self):
        self.data["password"] = "invalid_password"
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertRaises(InvalidCredentialsError)

    def test_token_create(self):
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)
        self.assertIn("refresh_token", response.cookies)
