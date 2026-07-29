"""Account authentication: password hashing, JWT sessions, and plan config."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import UTC, datetime, timedelta
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


def create_access_token(*, user_id: str, email: str, token_version: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "email": email,
        "tv": token_version,
        "iat": now,
        "exp": now + _ACCESS_TOKEN_TTL,
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
    except jwt.PyJWTError as error:
        raise TokenError(str(error)) from error


def generate_csrf_token(*, user_id: str, token_version: int) -> str:
    # Stateless, deterministic per (user, token_version) — the server can
    # always recompute the expected value without storing anything, and it
    # rotates automatically on logout (token_version bump) same as sessions.
    # Delivered via the JSON response body at signup/login/me, NOT a cookie:
    # frontend and backend live on different subdomains in production, and a
    # cookie set by the backend's origin is invisible to frontend JS via
    # document.cookie regardless of the httpOnly flag — a real double-submit
    # cookie can't work across that boundary.
    message = f"{user_id}:{token_version}".encode()
    return hmac.new(_jwt_secret().encode("utf-8"), message, hashlib.sha256).hexdigest()


def current_period() -> str:
    return datetime.now(UTC).strftime("%Y-%m")
