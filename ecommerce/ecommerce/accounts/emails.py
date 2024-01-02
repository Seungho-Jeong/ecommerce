from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from ..celeryconf import app
from .models import User


def send_account_confirmation_email(user: User, pin: str) -> None:
    """지정된 사용자에 대한 계정 확인 이메일 전송을 트리거합니다."""
    _send_account_confirmation_email.delay(user, user.email, pin)


@app.task
def _send_account_confirmation_email(user: User, email: str, pin: str) -> None:
    """실제로 계정 확인 이메일을 전송합니다."""
    send_mail(
        subject="Verify your account",
        message=f"Enter this code to verify your account: {pin}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
    user.pin_sent_at = timezone.now()
    user.save(update_fields=["pin_sent_at"])
