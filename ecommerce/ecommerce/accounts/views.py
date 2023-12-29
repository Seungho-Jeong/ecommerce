from django.conf import settings
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from . import emails
from .models import User
from .serializers import (
    AccountConfirmationSerializer,
    AccountRegisterSerializer,
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
