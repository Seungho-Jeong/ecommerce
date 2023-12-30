from django.conf import settings
from django.middleware.csrf import _get_new_csrf_token
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from . import emails
from .jwt import create_access_token, create_refresh_token
from .models import User
from .serializers import (
    AccountConfirmationSerializer,
    AccountRegisterSerializer,
    TokenCreateSerializer,
)


class AccountRegisterView(generics.CreateAPIView):
    serializer_class = AccountRegisterSerializer
    permission_classes = (AllowAny,)
    queryset = User.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(e.detail, status=e.status_code)

        user = serializer.save()
        if settings.ENABLE_CONFIRMATION_BY_EMAIL:
            pin = serializer.generate_pin()
            emails.send_account_confirmation_email(user, pin)
        else:
            serializer.confirm(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AccountConfirmationView(generics.CreateAPIView):
    serializer_class = AccountConfirmationSerializer
    permission_classes = (AllowAny,)
    queryset = User.objects.all()

    def post(self, request, *args, **kwargs):
        try:
            user = User.objects.get(email=request.data["email"])
        except User.DoesNotExist:
            return Response(
                {"email": "User with this email does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(user, data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(e.detail, status=e.status_code)

        serializer.confirm()
        return Response(serializer.data, status=status.HTTP_200_OK)


class TokenCreateView(generics.CreateAPIView):
    serializer_class = TokenCreateSerializer
    permission_classes = (AllowAny,)
    queryset = User.objects.all()

    def _retrieve_user_from_credentials(
        self, email: str, password: str
    ) -> User | None:
        """자격 증명을 사용하여 사용자를 검색합니다."""
        user = User.objects.filter(email=email, is_active=True).first()
        if user and user.check_password(password):
            return user
        return None

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(e.detail, status=e.status_code)

        user = self._retrieve_user_from_credentials(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)
        data = {
            "user": user.uuid,
            "token": access_token,
            "refresh_token": refresh_token,
            "csrf": _get_new_csrf_token(),
        }
        response = Response(data, status=status.HTTP_200_OK)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="lax",
            secure=settings.SECURE_SSL_REDIRECT,
        )
        response["X-CSRFToken"] = _get_new_csrf_token()
        response["Access-Control-Expose-Headers"] = "X-CSRFToken"
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Origin"] = settings.CLIENT_HOST
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
