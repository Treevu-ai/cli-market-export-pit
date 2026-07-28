"""Account authentication: password hashing, JWT sessions, and plan config."""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

PLANS: dict[str, dict[str, Any]] = {
    "free": {"name": "Free", "price": 0, "monthly_limit": 5},
    "pro": {"name": "Pro", "price": 49, "monthly_limit": 50},
    "enterprise": {"name": "Enterprise", "price": None, "monthly_limit": None},
}

_ACCESS_TOKEN_TTL = timedelta(days=7)

VERIFICATION_TOKEN_TTL = timedelta(hours=24)
DEFAULT_TIER_DURATION_DAYS: dict[str, int] = {"pro": 30, "enterprise": 30}


def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)


class TokenError(RuntimeError):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _jwt_secret() -> str:
    secret = os.getenv("PIT_JWT_SECRET")
    if not secret:
        raise TokenError("PIT_JWT_SECRET is not configured")
    return secret


def create_access_token(*, user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + _ACCESS_TOKEN_TTL,
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
    except jwt.PyJWTError as error:
        raise TokenError(str(error)) from error


def current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")
