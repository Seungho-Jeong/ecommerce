from typing import Any

import jwt
from django.conf import settings
from django.utils.timezone import datetime, timedelta

from .models import User

JWT_ALGORITHM = "HS256"
JWT_ACCESS_TYPE = "access"
JWT_REFRESH_TYPE = "refresh"


def jwt_base_payload(exp_delta: timedelta) -> dict[str, Any]:
    utc_now = datetime.utcnow()
    return {"iat": utc_now, "exp": utc_now + exp_delta}


def jwt_encode(payload: dict[str, Any]) -> str:
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def jwt_decode(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=JWT_ALGORITHM,
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
            "user_id": user.uuid,
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
        user, JWT_ACCESS_TYPE, settings.JWT_TTL_ACCESS, additional_payload
    )
    return jwt_encode(payload)


def create_refresh_token(
    user: User, additional_payload: dict[str, Any] | None = None
) -> str:
    payload = jwt_user_payload(
        user, JWT_REFRESH_TYPE, settings.JWT_TTL_REFRESH, additional_payload
    )
    return jwt_encode(payload)
