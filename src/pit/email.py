"""Transactional email via Resend — currently used only for signup verification."""

from __future__ import annotations

import json
import logging
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


class EmailSendError(RuntimeError):
    pass


def _resend_from() -> str:
    return os.getenv("RESEND_FROM_EMAIL", "CLI Market PIT <hello@cli-market.dev>")


def _frontend_url() -> str:
    return os.getenv("PIT_FRONTEND_URL", "https://cli-market-pit.fly.dev").rstrip("/")


def send_verification_email(*, to: str, token: str) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.error("RESEND_API_KEY not configured; verification email to %s was NOT sent", to)
        return
    verify_url = f"{_frontend_url()}/verify?token={token}"
    body = {
        "from": _resend_from(),
        "to": [to],
        "subject": "Verifica tu cuenta — CLI Market PIT",
        "html": (
            "<p>Confirma tu correo para empezar a usar CLI Market PIT.</p>"
            f'<p><a href="{verify_url}">Verificar mi cuenta</a></p>'
            "<p>Este link expira en 24 horas.</p>"
        ),
    }
    request = Request(
        RESEND_API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=15):
            pass
    except HTTPError as error:
        raise EmailSendError(f"Resend returned HTTP {error.code}: {error.read()!r}") from error
    except URLError as error:
        raise EmailSendError(f"Resend network error: {error.reason}") from error
