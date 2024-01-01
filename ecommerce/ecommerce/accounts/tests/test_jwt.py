from django.utils.timezone import timedelta
from rest_framework.test import APIClient, APITestCase, override_settings

from ..jwt import (
    create_access_token,
    create_refresh_token,
    jwt_base_payload,
    jwt_decode,
    jwt_encode,
    jwt_user_payload,
)
from ..models import User


class JWTTest(APITestCase):
    """JWT 테스트"""

    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com",
            password="test1234!!",
            username="test_user",
            is_active=True,
        )

    def test_jwt_base_payload(self):
        exp_delta = timedelta(minutes=5)
        payload = jwt_base_payload(exp_delta)
        self.assertIn("iat", payload)
        self.assertIn("exp", payload)

    def test_jwt_encode_decode(self):
        payload = {"test": "test"}
        token = jwt_encode(payload)
        self.assertIsInstance(token, str)

        decoded_payload = jwt_decode(token)
        self.assertEqual(payload, decoded_payload)

    @override_settings(
        JWT_TTL_ACCESS=timedelta(seconds=300), JWT_ACCESS_TYPE="test"
    )
    def test_jwt_user_payload(self):
        payload = jwt_user_payload(self.user, "test", timedelta(minutes=5))
        self.assertEqual(payload["token"], self.user.jwt_token_key)
        self.assertEqual(payload["email"], self.user.email)
        self.assertEqual(payload["type"], "test")
        self.assertEqual(payload["user_id"], str(self.user.uuid))
        self.assertEqual(payload["is_staff"], self.user.is_staff)

    @override_settings(
        JWT_TTL_ACCESS=timedelta(seconds=300), JWT_ACCESS_TYPE="test"
    )
    def test_create_access_token(self):
        token = create_access_token(self.user)
        self.assertIsInstance(token, str)

        payload = jwt_decode(token)
        self.assertEqual(payload["token"], self.user.jwt_token_key)
        self.assertEqual(payload["email"], self.user.email)
        self.assertEqual(payload["type"], "test")
        self.assertEqual(payload["user_id"], str(self.user.uuid))
        self.assertEqual(payload["is_staff"], self.user.is_staff)

    @override_settings(
        JWT_TTL_REFRESH=timedelta(seconds=300), JWT_REFRESH_TYPE="test"
    )
    def test_create_refresh_token(self):
        token = create_refresh_token(self.user)
        self.assertIsInstance(token, str)

        payload = jwt_decode(token)
        self.assertEqual(payload["token"], self.user.jwt_token_key)
        self.assertEqual(payload["email"], self.user.email)
        self.assertEqual(payload["type"], "test")
        self.assertEqual(payload["user_id"], str(self.user.uuid))
        self.assertEqual(payload["is_staff"], self.user.is_staff)
