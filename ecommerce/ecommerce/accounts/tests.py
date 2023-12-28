from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import User


class AccountRegisterViewTestCase(APITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()
        self.model = User

    def test_register_account(self):
        url = reverse("signup")
        data = {
            "email": "test1@test.com",
            "password": "test1234",
            "username": "test_user",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.model.objects.count(), 1)
        self.assertEqual(self.model.objects.get().email, data["email"])
        self.assertEqual(self.model.objects.get().username, data["username"])
        self.assertTrue(
            self.model.objects.get().check_password(data["password"])
        )
        self.assertEqual(self.model.objects.get().is_active, False)
        self.assertEqual(self.model.objects.get().is_staff, False)
        self.assertEqual(self.model.objects.get().is_superuser, False)
        self.assertEqual(self.model.objects.get().groups.count(), 0)
        self.assertEqual(self.model.objects.get().user_permissions.count(), 0)

    def test_register_account_with_invalid_password(self):
        url = reverse("signup")
        data = {
            "email": "test1@test.com",
            "password": "test",
            "username": "test_user",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.model.objects.count(), 0)
