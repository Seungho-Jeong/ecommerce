from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, override_settings

from ..exceptions import (
    ExpiredPinError,
    InvalidCredentialsError,
    InvalidPinError,
    JWTInvalidTokenError,
    PasswordValidationError,
    TooManyPinAttemptsError,
)
from ..models import User
from ..serializers import (
    AccountConfirmationSerializer,
    AccountRegisterSerializer,
    TokenCreateSerializer,
    TokenRefreshSerializer,
    TokenVerifySerializer,
)
from ..services import AccountService


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

    def test_validate_invalid_email(self):
        serializer = self.serializer(data=self.data)
        self.assertTrue(serializer.is_valid())

        self.data["email"] = "invalid_mail_format.com"
        serializer = self.serializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "Enter a valid email address.", serializer.errors["email"]
        )

    def test_validate_invalid_password(self):
        serializer = self.serializer(data=self.data)
        self.assertTrue(serializer.is_valid())

        self.data["password"] = "short"
        serializer = self.serializer(data=self.data)
        self.assertFalse(serializer.is_valid())

        with self.assertRaises(PasswordValidationError):
            serializer.validate_password(self.data["password"])

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

    def test_validate_invalid_pin(self):
        serializer = self.serializer(instance=self.user, data=self.data)
        self.assertTrue(serializer.is_valid())

        self.data["pin"] = "000000"
        serializer = self.serializer(instance=self.user, data=self.data)
        self.assertFalse(serializer.is_valid())

        with self.assertRaises(InvalidPinError):
            serializer.validate_pin(self.data["pin"])

    @override_settings(PIN_EXPIRE_TIMEDELTA_SECONDS=60)
    def test_validate_pin_expired(self):
        serializer = self.serializer(instance=self.user, data=self.data)
        self.assertTrue(serializer.is_valid())

        self.user.pin_sent_at = timezone.now() - timezone.timedelta(seconds=60)
        self.user.save()
        serializer = self.serializer(instance=self.user, data=self.data)
        self.assertFalse(serializer.is_valid())

        with self.assertRaises(ExpiredPinError):
            serializer.validate_pin(self.data["pin"])

    @override_settings(PIN_FAILURES_LIMIT=5)
    def test_validate_pin_failures_limit(self):
        serializer = self.serializer(instance=self.user, data=self.data)
        self.assertTrue(serializer.is_valid())

        self.user.pin_failures = 5
        self.user.save()
        serializer = self.serializer(instance=self.user, data=self.data)
        self.assertFalse(serializer.is_valid())

        with self.assertRaises(TooManyPinAttemptsError):
            serializer.validate_pin(self.data["pin"])

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

    def test_validate_invalid_email(self):
        serializer = self.serializer(data=self.data)
        self.assertTrue(serializer.is_valid())

        self.data["email"] = "invalid_mail_format.com"
        serializer = self.serializer(data=self.data)
        self.assertFalse(serializer.is_valid())

        with self.assertRaises(InvalidCredentialsError):
            serializer.validate_email(self.data["email"])

    def test_validate_invalid_password(self):
        serializer = self.serializer(data=self.data)
        self.assertTrue(serializer.is_valid())

        self.data["password"] = "short"
        serializer = self.serializer(data=self.data)
        self.assertFalse(serializer.is_valid())

        with self.assertRaises(PasswordValidationError):
            serializer.validate_password(self.data["password"])

    def test_invalid_credentials(self):
        self.data["password"] = "invalid_password"
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(JWT_ACCESS_TYPE="access", JWT_REFRESH_TYPE="refresh")
    def test_token_create(self):
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("refresh", response.cookies)


class TokenVerifyViewTestCase(APITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()
        self.token_url = reverse("signin")
        self.url = reverse("token_verify")
        self.model = User
        self.serializer = TokenVerifySerializer

        self.user = self.model.objects.create_user(
            email="test@test.com",
            password="test1234!!",
            username="test_user",
            is_active=True,
        )
        self.service = AccountService(self.serializer)
        self.tokens = self.service.create_tokens(self.user)
        self.data = {"token": self.tokens["access"]}

    def test_serializer(self):
        serializer = self.serializer(data=self.data)
        self.assertTrue(serializer.is_valid())

    def test_validate_invalid_token(self):
        serializer = self.serializer(data=self.data)
        self.assertTrue(serializer.is_valid())

        self.data["token"] = "invalid_token"
        with self.assertRaises(JWTInvalidTokenError):
            serializer = self.serializer(data=self.data)
            self.assertFalse(serializer.is_valid())

    def test_token_verify(self):
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(JWT_TTL_ACCESS=timezone.timedelta(seconds=0))
    def test_expired_token(self):
        self.tokens = self.service.create_tokens(self.user)
        self.data["token"] = self.tokens["access"]
        response = self.client.post(self.url, self.data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn(
            str(JWTInvalidTokenError.default_detail), response.data["detail"]
        )

    def test_invalid_token(self):
        self.data["token"] = "invalid_token"
        response = self.client.post(self.url, self.data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn(
            str(JWTInvalidTokenError.default_detail), response.data["detail"]
        )

    def test_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(self.url, self.data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn(
            str(JWTInvalidTokenError.default_detail), response.data["detail"]
        )


class TokenRefreshViewTestCase(APITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()
        self.token_url = reverse("signin")
        self.url = reverse("token_refresh")
        self.model = User
        self.serializer = TokenRefreshSerializer

        self.user = self.model.objects.create_user(
            email="test@test.com",
            password="test1234!!",
            username="test_user",
            is_active=True,
        )
        self.service = AccountService(self.serializer)
        self.tokens = self.service.create_tokens(self.user)
        self.access_token = self.tokens["access"]
        self.refresh_token = self.tokens["refresh"]
        self.data = {"token": self.refresh_token}

    def test_serializer(self):
        serializer = self.serializer(data=self.data)
        self.assertTrue(serializer.is_valid())

    def test_validate_invalid_token(self):
        serializer = self.serializer(data=self.data)
        self.assertTrue(serializer.is_valid())

        self.data["token"] = "invalid_token"
        with self.assertRaises(JWTInvalidTokenError):
            serializer = self.serializer(data=self.data)
            self.assertFalse(serializer.is_valid())

    def test_token_refresh(self):
        refresh_time = timezone.datetime.utcnow() + timezone.timedelta(
            seconds=1
        )
        with freeze_time(refresh_time):
            response = self.client.post(self.url, self.data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("access", response.data)
            self.assertNotEqual(self.access_token, response.data["access"])

    @override_settings(JWT_TTL_REFRESH=timezone.timedelta(seconds=0))
    def test_expired_token(self):
        self.tokens = self.service.create_tokens(self.user)
        self.data["token"] = self.tokens["refresh"]
        response = self.client.post(self.url, self.data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn(
            str(JWTInvalidTokenError.default_detail), response.data["detail"]
        )

    def test_invalid_token(self):
        self.data["token"] = "invalid_token"
        response = self.client.post(self.url, self.data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn(
            str(JWTInvalidTokenError.default_detail), response.data["detail"]
        )

    def test_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(self.url, self.data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn(
            str(JWTInvalidTokenError.default_detail), response.data["detail"]
        )
