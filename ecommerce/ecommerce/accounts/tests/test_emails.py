from unittest.mock import patch

from django.core import mail
from django.utils.crypto import get_random_string
from rest_framework.test import APIClient, APITestCase

from .. import emails
from ..models import User


class AccountEmailTestCase(APITestCase):
    """계정 이메일 테스트"""

    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()
        self.staff_user = User.objects.create_superuser(
            email="admin@test.com",
            password="password1234!!",
            username="admin",
        )
        self.user = User.objects.create_user(
            email="test@test.com",
            password="test1234!!",
            username="test_user",
        )

    def test_send_account_confirmation_email(self):
        pin = get_random_string(length=6, allowed_chars="0123456789")
        emails._send_account_confirmation_email(
            self.user, self.user.email, pin
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Verify your account")
        self.assertEqual(
            mail.outbox[0].body,
            f"Enter this code to verify your account: {pin}",
        )
