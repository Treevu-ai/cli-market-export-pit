"""Transactional email via Resend — currently used only for signup verification."""

from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"

_VERIFICATION_COPY: dict[str, dict[str, str]] = {
    "es": {
        "subject": "Confirma tu cuenta — CLI Market PIT",
        "eyebrow": "CLI Market &middot; Motor PIT",
        "heading": "Confirma tu cuenta",
        "intro": (
            "Gracias por registrarte en CLI Market PIT, el motor que valida tu producto con "
            "evidencia científica, comercial y regulatoria antes de que inviertas en exportarlo."
        ),
        "cta_lead": "Confirma tu correo para activar tu cuenta y correr tu primer análisis:",
        "cta_button": "Verificar mi cuenta",
        "expiry": "Este link expira en 24 horas.",
        "ignore": "Si no creaste esta cuenta, puedes ignorar este correo.",
    },
    "en": {
        "subject": "Confirm your account — CLI Market PIT",
        "eyebrow": "CLI Market &middot; PIT Engine",
        "heading": "Confirm your account",
        "intro": (
            "Thanks for signing up for CLI Market PIT, the engine that validates your product with "
            "scientific, commercial, and regulatory evidence before you invest in exporting it."
        ),
        "cta_lead": "Confirm your email to activate your account and run your first analysis:",
        "cta_button": "Verify my account",
        "expiry": "This link expires in 24 hours.",
        "ignore": "If you didn't create this account, you can ignore this email.",
    },
}


class EmailSendError(RuntimeError):
    pass


def _resend_from() -> str:
    return os.getenv("RESEND_FROM_EMAIL", "CLI Market PIT <hello@cli-market.dev>")


def _frontend_url() -> str:
    return os.getenv("PIT_FRONTEND_URL", "https://cli-market-pit.fly.dev").rstrip("/")


def _copy(locale: str) -> dict[str, str]:
    return _VERIFICATION_COPY.get(locale, _VERIFICATION_COPY["es"])


def _verification_email_html(verify_url: str, copy: dict[str, str]) -> str:
    return f"""
<div style="font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; max-width: 480px; margin: 0 auto; padding: 40px 24px;">
  <p style="font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: #64748b; margin: 0 0 28px;">{copy["eyebrow"]}</p>
  <h1 style="font-size: 20px; margin: 0 0 16px; color: #0f172a;">{copy["heading"]}</h1>
  <p style="font-size: 14px; line-height: 1.6; color: #334155; margin: 0 0 20px;">
    {copy["intro"]}
  </p>
  <p style="font-size: 14px; line-height: 1.6; color: #334155; margin: 0 0 28px;">
    {copy["cta_lead"]}
  </p>
  <p style="margin: 0 0 28px;">
    <a href="{verify_url}" style="display: inline-block; background: #0f172a; color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 999px; font-size: 14px; font-weight: 500;">{copy["cta_button"]}</a>
  </p>
  <p style="font-size: 13px; color: #64748b; margin: 0 0 4px;">{copy["expiry"]}</p>
  <p style="font-size: 13px; color: #64748b; margin: 0;">{copy["ignore"]}</p>
</div>
""".strip()


def _verification_email_text(verify_url: str, copy: dict[str, str]) -> str:
    eyebrow_plain = copy["eyebrow"].replace("&middot;", "·")
    return (
        f"{eyebrow_plain}\n\n"
        f"{copy['heading']}\n\n"
        f"{copy['intro']}\n\n"
        f"{copy['cta_lead']} {verify_url}\n\n"
        f"{copy['expiry']} {copy['ignore']}"
    )


def send_verification_email(*, to: str, token: str, locale: str = "es") -> None:
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.error("RESEND_API_KEY not configured; verification email to %s was NOT sent", to)
        return
    copy = _copy(locale)
    verify_url = f"{_frontend_url()}/verify?token={token}"
    body: dict[str, Any] = {
        "from": _resend_from(),
        "to": [to],
        "subject": copy["subject"],
        "html": _verification_email_html(verify_url, copy),
        "text": _verification_email_text(verify_url, copy),
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
