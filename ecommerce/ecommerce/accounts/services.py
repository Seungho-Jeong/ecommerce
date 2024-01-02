from django.conf import settings

from . import emails
from .models import User


class AccountService:
    def __init__(self, serializer, request=None):
        self.serializer = serializer
        self.request = request

    def create_user(self) -> User:
        """사용자를 생성하고 이메일 인증이 활성화되어 있으면 이메일을 보냅니다."""
        instance = self.serializer.save()
        if settings.ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL:
            pin = instance.set_pin()
            emails.send_account_confirmation_email(instance, pin)
        else:
            instance.activate()
        return instance
