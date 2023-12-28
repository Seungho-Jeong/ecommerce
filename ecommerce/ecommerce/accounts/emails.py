from django.core.mail import send_mail

from ..celeryconf import app
from .models import User


def send_account_confirmation_email(user: User, pin: str) -> None:
    """지정된 사용자에 대한 계정 확인 이메일 전송을 트리거합니다."""
    _send_account_confirmation_email.delay(user.email, pin)


@app.task
def _send_account_confirmation_email(email: str, pin: str) -> None:
    """실제로 계정 확인 이메일을 전송합니다."""
    send_mail(
        subject="Verify your account",
        html_message=f"<H2>Verify your account</H2><br/><p>Enter this code to verify your account: <strong>{pin}</strong></p>",
        recipient_list=[email],
        fail_silently=False,
    )
