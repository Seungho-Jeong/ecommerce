from django.conf import settings
from django.middleware.csrf import _get_new_csrf_string
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from . import emails
from .jwt import create_access_token, create_refresh_token
from .models import User
from .serializers import (
    AccountConfirmationSerializer,
    AccountRegisterSerializer,
    TokenCreateSerializer,
    TokenRefreshSerializer,
    TokenVerifySerializer,
)
from .services import AccountService


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

        account_service = AccountService(serializer, request)
        account_service.create_user()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AccountConfirmationView(generics.GenericAPIView):
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
        user.activate()
        return Response(serializer.data, status=status.HTTP_200_OK)


class TokenCreateView(generics.GenericAPIView):
    serializer_class = TokenCreateSerializer
    permission_classes = (AllowAny,)
    queryset = User.objects.all()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(e.detail, status=e.status_code)

        account_service = AccountService(serializer, request)
        user = account_service.get_user()
        tokens = account_service.create_tokens(user)

        response = Response(tokens, status=status.HTTP_200_OK)
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,
            samesite="lax",
            secure=settings.SECURE_SSL_REDIRECT,
        )
        return response


class TokenVerifyView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TokenVerifySerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response(e.detail, status=e.status_code)
        return Response(serializer.data, status=status.HTTP_200_OK)
