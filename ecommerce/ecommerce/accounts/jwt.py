from typing import Any

import jwt
from django.conf import settings
from django.utils.timezone import datetime, timedelta

from .exceptions import (
    JWTDecodeError,
    JWTInvalidTokenError,
    JWTTokenSignatureExpiredError,
)
from .models import User


def jwt_base_payload(exp_delta: timedelta) -> dict[str, Any]:
    utc_now = datetime.utcnow()
    return {"iat": utc_now, "exp": utc_now + exp_delta}


def jwt_encode(payload: dict[str, Any]) -> str:
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def jwt_decode(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=settings.JWT_ALGORITHM,
    )


def jwt_user_payload(
    user: User,
    token_type: str,
    exp_delta: timedelta,
    additional_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = jwt_base_payload(exp_delta)
    payload.update(
        {
            "token": user.jwt_token_key,
            "email": user.email,
            "type": token_type,
            "user_id": str(user.uuid),
            "is_staff": user.is_staff,
        }
    )
    if additional_payload:
        payload.update(additional_payload)
    return payload


def create_access_token(
    user: User, additional_payload: dict[str, Any] | None = None
) -> str:
    payload = jwt_user_payload(
        user,
        settings.JWT_ACCESS_TYPE,
        settings.JWT_TTL_ACCESS,
        additional_payload,
    )
    return jwt_encode(payload)


def create_refresh_token(
    user: User, additional_payload: dict[str, Any] | None = None
) -> str:
    payload = jwt_user_payload(
        user,
        settings.JWT_REFRESH_TYPE,
        settings.JWT_TTL_REFRESH,
        additional_payload,
    )
    return jwt_encode(payload)


def get_payload(token: str) -> dict[str, Any]:
    """JWT 토큰의 payload를 가져온다."""
    try:
        payload = jwt_decode(token)
    except jwt.ExpiredSignatureError:
        raise JWTTokenSignatureExpiredError
    except jwt.DecodeError:
        raise JWTDecodeError
    except jwt.InvalidTokenError:
        raise JWTInvalidTokenError
    return payload


def get_user_from_payload(payload: dict[str, Any]) -> User:
    """JWT 토큰의 payload로부터 유저를 가져온다."""
    user = User.objects.filter(email=payload["email"], is_active=True).first()
    jwt_token_key = payload.get("token")
    if not user or not jwt_token_key or user.jwt_token_key != jwt_token_key:
        raise JWTInvalidTokenError
    return user
