from django.conf import settings
from rest_framework.authentication import BaseAuthentication

from .exceptions import DoesNotExistUserError, JWTInvalidTokenError
from .jwt import get_user_from_payload, jwt_decode
from .models import User


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        """토큰을 확인하고 사용자를 반환합니다."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        try:
            token = auth_header.split(" ")[1]
            payload = jwt_decode(token)
        except Exception:
            raise JWTInvalidTokenError

        try:
            user = get_user_from_payload(payload)
        except User.DoesNotExist:
            raise DoesNotExistUserError

        return (user, None)

    def authenticate_header(self, request):
        """인증 헤더를 반환합니다."""
        return (
            f"{settings.AUTH_HEADER_TYPE} realm={settings.AUTH_HEADER_REALM}"
        )
