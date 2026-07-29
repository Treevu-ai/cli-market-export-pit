"""FastAPI entry point for PIT research runs."""

from __future__ import annotations

import ipaddress
import json
import logging
import os
import secrets
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any


def _load_env_file() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


_load_env_file()

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field, field_validator

from . import auth
from . import email as email_service
from .bcrp import BCRPConnector
from .climarket import CLIMarketConnector
from .climatiq import ClimatiqConnector
from .comtrade import ComtradeConnector
from .cordis import CORDISConnector
from .crossref import CrossrefConnector
from .efsa_eurlex import EFSALexConnector
from .epo_ops import EPOOPSConnector
from .fooddata_central import FoodDataCentralConnector
from .gdelt import GDELTConnector
from .nih_reporter import NIHReporterConnector
from .nsf_awards import NSFAwardsConnector
from .openalex import OpenAlexConnector
from .openfda import OpenFDAConnector
from .pubmed import PubMedConnector
from .reports import ReportGenerator
from .research import ResearchExecutionError, ResearchService
from .scoring import ScoringService
from .semanticscholar import SemanticScholarConnector
from .storage import ResearchStore

logger = logging.getLogger("pit")

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = REPO_ROOT / "web"
ASSETS_DIR = REPO_ROOT / "assets"

ENRICHMENT_HANDLERS: dict[str, str] = {
    "crossref": "enrich_with_crossref",
    "pubmed": "enrich_with_pubmed",
    "semanticscholar": "enrich_with_semanticscholar",
    "patent": "enrich_with_patent",
    "trend": "enrich_with_trend",
    "trade": "enrich_with_trade",
    "regulatory": "enrich_with_regulatory",
    "sustainability": "enrich_with_sustainability",
    "techscout": "enrich_with_techscout",
    "commerce": "enrich_with_commerce",
}


class ResearchRunCreate(BaseModel):
    query: Annotated[str, Field(min_length=3, max_length=300)]
    target_market: Annotated[str, Field(pattern=r"^[A-Z]{2}$")] = "US"
    application: Annotated[str, Field(min_length=3, max_length=200)] = "functional foods and beverages"
    from_publication_date: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")] = "2021-01-01"
    limit: Annotated[int, Field(ge=1, le=100)] = 25


class ResearchRunFullCreate(ResearchRunCreate):
    hs_code: Annotated[str | None, Field(min_length=2, max_length=20)] = None


class DomainEnrichmentCreate(BaseModel):
    limit: Annotated[int, Field(ge=1, le=100)] = 25
    hs_code: Annotated[str | None, Field(min_length=2, max_length=20)] = None


class FichaCreate(BaseModel):
    segment: Annotated[str, Field(min_length=2, max_length=200)] = "exportadores y retail premium"
    stage: Annotated[str, Field(min_length=2, max_length=80)] = "concepto"
    market_label: Annotated[str | None, Field(max_length=120)] = None


_PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`\"'\\"


def _validate_password_strength(password: str) -> str:
    if any(char.isspace() for char in password):
        raise ValueError("password must not contain spaces")
    if not any(char.isupper() for char in password):
        raise ValueError("password must contain at least one uppercase letter")
    if not any(char.islower() for char in password):
        raise ValueError("password must contain at least one lowercase letter")
    if not any(char.isdigit() for char in password):
        raise ValueError("password must contain at least one digit")
    if not any(char in _PASSWORD_SPECIAL_CHARS for char in password):
        raise ValueError("password must contain at least one special character (e.g. # % ! @)")
    return password


class SignupCreate(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=200)]
    locale: Annotated[str, Field(pattern=r"^(es|en)$")] = "es"

    _validate_password = field_validator("password")(_validate_password_strength)


class LoginCreate(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=200)]


class SetTierCreate(BaseModel):
    email: EmailStr
    tier: Annotated[str, Field(pattern=r"^(free|pro|enterprise)$")]
    expires_in_days: Annotated[int, Field(ge=1, le=3650)] | None = None


def _default_services() -> tuple[ResearchService, ScoringService, ReportGenerator]:
    database_path = Path(os.getenv("PIT_DB_PATH", "data/pit.db"))
    raw_directory = Path(os.getenv("PIT_RAW_DIR", "data/raw"))
    patent_connector = None
    if os.getenv("EPO_OPS_CONSUMER_KEY") and os.getenv("EPO_OPS_CONSUMER_SECRET"):
        patent_connector = EPOOPSConnector(
            os.getenv("EPO_OPS_CONSUMER_KEY", ""),
            os.getenv("EPO_OPS_CONSUMER_SECRET", ""),
        )
    store = ResearchStore(database_path, raw_directory)
    service = ResearchService(
        store,
        OpenAlexConnector(),
        CrossrefConnector(os.getenv("PIT_CONTACT_EMAIL")),
        PubMedConnector(),
        SemanticScholarConnector(),
        patent_connector,
        GDELTConnector(),
        ComtradeConnector(),
        CORDISConnector(),
        NIHReporterConnector(),
        NSFAwardsConnector(),
        OpenFDAConnector(),
        EFSALexConnector(),
        FoodDataCentralConnector(api_key=os.getenv("FOODDATA_CENTRAL_API_KEY")),
        ClimatiqConnector(api_key=os.getenv("CLIMATIQ_API_KEY")),
        CLIMarketConnector(),
        BCRPConnector(),
    )
    return service, ScoringService(store), ReportGenerator()


_ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("PIT_CORS_ORIGINS", "").split(",") if origin.strip()]


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "path": record.pathname,
            "line": record.lineno,
        }
        if record.exc_info:
            log_entry["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def _setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class Metrics:
    def __init__(self) -> None:
        self.requests_total = 0
        self.requests_by_endpoint: dict[str, int] = {}
        self.errors_total = 0
        self.errors_by_endpoint: dict[str, int] = {}
        self.request_duration_sum = 0.0
        self.request_duration_count = 0

    def record_request(self, endpoint: str, duration: float, status_code: int) -> None:
        self.requests_total += 1
        self.requests_by_endpoint[endpoint] = self.requests_by_endpoint.get(endpoint, 0) + 1
        self.request_duration_sum += duration
        self.request_duration_count += 1
        if status_code >= 400:
            self.errors_total += 1
            self.errors_by_endpoint[endpoint] = self.errors_by_endpoint.get(endpoint, 0) + 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "requests_total": self.requests_total,
            "requests_by_endpoint": self.requests_by_endpoint,
            "errors_total": self.errors_total,
            "errors_by_endpoint": self.errors_by_endpoint,
            "avg_duration_seconds": self.request_duration_sum / self.request_duration_count if self.request_duration_count else 0.0,
        }


_metrics = Metrics()


class RequestMetricsMiddleware:
    """Records request duration/status for /metrics. Auth is handled per-route
    via the `get_current_user`/`require_quota` dependencies, not here."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        start_time = time.perf_counter()
        status_code_holder = {"status_code": 200}

        async def send_wrapper(message: Any) -> None:
            if message["type"] == "http.response.start":
                status_code_holder["status_code"] = message["status"]
            await send(message)

        await self.app(scope, receive, send_wrapper)
        duration = time.perf_counter() - start_time
        endpoint = scope["path"]
        _metrics.record_request(endpoint, duration, status_code_holder["status_code"])
        logger.info("request", extra={"endpoint": endpoint, "method": scope["method"], "status": status_code_holder["status_code"], "duration": round(duration, 4)})


def _envelope(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "data": data,
        "meta": {
            "confidence": "ok",
            "evidence_count": len(data.get("evidence", [])),
        },
        "trace": {
            "version": "0.1.0",
            "timestamp": datetime.now(UTC).isoformat(),
        },
    }


def _handle_research_error(error: ResearchExecutionError) -> None:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={"research_run_id": error.run_id, "message": error.message},
    ) from error


def _check_run_ownership(run: dict[str, Any], user: dict[str, Any]) -> None:
    # 404, not 403: a non-owner should not be able to distinguish "run exists
    # but isn't yours" from "run doesn't exist" — that alone leaks information.
    if run.get("user_id") != user["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")


def create_app(
    service: ResearchService | None = None,
    scoring_service: ScoringService | None = None,
    report_generator: ReportGenerator | None = None,
) -> FastAPI:
    default_service, default_scoring, default_report = _default_services()
    research_service = service or default_service
    scoring_svc = scoring_service or (ScoringService(research_service.store) if service else default_scoring)
    report_gen = report_generator or default_report
    app = FastAPI(
        title="PIT Research API",
        version="0.1.0",
        description="Traceable technology-intelligence research runs.",
    )
    app.add_middleware(RequestMetricsMiddleware)
    if _ALLOWED_ORIGINS:
        from starlette.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=_ALLOWED_ORIGINS,
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )
    _setup_logging()

    def get_current_user(request: Request) -> dict[str, Any]:
        token: str | None = None
        authorization = request.headers.get("authorization")
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1]
        if token is None:
            token = request.cookies.get("pit_session")
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        try:
            payload = auth.decode_access_token(token)
        except auth.TokenError as error:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session") from error
        user = research_service.store.get_user_by_id(payload["sub"])
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        if payload.get("tv") != user["token_version"]:
            # Token predates the account's current token_version — either
            # revoked by a logout since this token was issued, or forged.
            # Same error as an expired token: revoked and expired should be
            # indistinguishable to a caller.
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
        return research_service.store.downgrade_expired_tier(user)

    def require_quota(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if not user["email_verified"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "email_not_verified", "message": "Verify your email before running analyses"},
            )
        plan = auth.PLANS.get(user["tier"], auth.PLANS["free"])
        limit = plan["monthly_limit"]
        period = auth.current_period()
        new_count = research_service.store.get_and_increment_usage(user_id=user["id"], period=period, limit=limit)
        if new_count is None:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "message": "Monthly limit reached",
                    "tier": user["tier"],
                    "limit": limit,
                    "upgrade_url": "/pricing",
                },
            )
        return user

    def _set_session_cookie(response: Response, token: str) -> None:
        response.set_cookie(
            "pit_session",
            token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=7 * 24 * 3600,
        )

    def _verify_csrf(request: Request, user: dict[str, Any]) -> None:
        # Bearer-token clients (non-browser API consumers, and this project's
        # own test suite) aren't cookie-authenticated, so a cross-site page
        # can't ride their credentials — CSRF only applies to the ambient
        # pit_session cookie.
        authorization = request.headers.get("authorization")
        if authorization and authorization.lower().startswith("bearer "):
            return
        header_token = request.headers.get("x-csrf-token")
        expected = auth.generate_csrf_token(user_id=user["id"], token_version=user["token_version"])
        if not header_token or not secrets.compare_digest(header_token, expected):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing or invalid CSRF token")

    def require_csrf(request: Request, user: dict[str, Any] = Depends(get_current_user)) -> None:
        _verify_csrf(request, user)

    def require_admin(request: Request) -> None:
        admin_secret = os.getenv("PIT_ADMIN_SECRET")
        provided = request.headers.get("x-admin-secret")
        if not admin_secret or not provided or not secrets.compare_digest(provided, admin_secret):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin secret")

    SIGNUP_RATE_LIMIT_PER_IP = 5

    def _client_ip(request: Request) -> str:
        # Only trust Fly.io's own edge-injected header — it is stripped/overwritten
        # by Fly's proxy for any inbound request, so it cannot be spoofed by a client
        # sending its own copy. We deliberately do NOT fall back to X-Forwarded-For,
        # which is client-suppliable and would let an attacker forge a fresh "IP" on
        # every request to bypass this limiter entirely.
        fly_ip = request.headers.get("fly-client-ip")
        raw_ip = fly_ip or (request.client.host if request.client else "unknown")
        try:
            return ipaddress.ip_address(raw_ip).compressed
        except ValueError:
            return "unknown"

    def require_signup_rate_limit(request: Request) -> None:
        ip = _client_ip(request)
        window_key = datetime.now(UTC).strftime("%Y-%m-%dT%H")
        try:
            new_count = research_service.store.get_and_increment_signup_attempts(
                ip=ip, window_key=window_key, limit=SIGNUP_RATE_LIMIT_PER_IP
            )
        except Exception as error:
            logging.getLogger(__name__).error("signup rate limit check failed: %s", error)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Signup is temporarily unavailable. Please try again shortly.",
            ) from error
        if new_count is None:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many signup attempts from this address. Try again later.",
            )

    @app.get("/v1/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok", "version": "0.1.0"}

    def _new_verification_token() -> tuple[str, str]:
        token = auth.generate_verification_token()
        expires_at = (datetime.now(UTC) + auth.VERIFICATION_TOKEN_TTL).isoformat()
        return token, expires_at

    def _dispatch_verification_email(*, to: str, token: str, locale: str) -> None:
        try:
            email_service.send_verification_email(to=to, token=token, locale=locale)
        except email_service.EmailSendError as error:
            logging.getLogger(__name__).error("failed to send verification email to %s: %s", to, error)

    def _resend_verification_email(user: dict[str, Any]) -> None:
        token, expires_at = _new_verification_token()
        research_service.store.set_verification_token(user_id=user["id"], token=token, expires_at=expires_at)
        _dispatch_verification_email(to=user["email"], token=token, locale=user["locale"])

    @app.post("/v1/auth/signup", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_signup_rate_limit)])
    def signup(payload: SignupCreate, response: Response) -> dict[str, Any]:
        if research_service.store.get_user_by_email(payload.email) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        password_hash = auth.hash_password(payload.password)
        verification_token, verification_expires_at = _new_verification_token()
        user = research_service.store.create_user(
            email=payload.email,
            password_hash=password_hash,
            locale=payload.locale,
            verification_token=verification_token,
            verification_expires_at=verification_expires_at,
        )
        _dispatch_verification_email(to=user["email"], token=verification_token, locale=user["locale"])
        token = auth.create_access_token(user_id=user["id"], email=user["email"], token_version=user["token_version"])
        _set_session_cookie(response, token)
        csrf_token = auth.generate_csrf_token(user_id=user["id"], token_version=user["token_version"])
        return _envelope({"token": token, "csrf_token": csrf_token, "email": user["email"], "tier": user["tier"]})

    @app.get("/v1/auth/verify")
    def verify_email(token: str) -> dict[str, Any]:
        user = research_service.store.verify_email(token=token, now=datetime.now(UTC).isoformat())
        if user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification link")
        return _envelope({"email": user["email"], "email_verified": True})

    RESEND_VERIFICATION_LIMIT_PER_HOUR = 3

    @app.post("/v1/auth/resend-verification", dependencies=[Depends(require_csrf)])
    def resend_verification(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if user["email_verified"]:
            return _envelope({"already_verified": True})
        window_key = datetime.now(UTC).strftime("%Y-%m-%dT%H")
        new_count = research_service.store.get_and_increment_resend_attempts(
            user_id=user["id"], window_key=window_key, limit=RESEND_VERIFICATION_LIMIT_PER_HOUR
        )
        if new_count is None:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many resend attempts. Try again later.",
            )
        _resend_verification_email(user)
        return _envelope({"sent": True})

    LOGIN_RATE_LIMIT_PER_IP = 10

    def require_login_rate_limit(request: Request) -> None:
        ip = _client_ip(request)
        window_key = datetime.now(UTC).strftime("%Y-%m-%dT%H")
        try:
            new_count = research_service.store.get_and_increment_login_attempts(
                ip=ip, window_key=window_key, limit=LOGIN_RATE_LIMIT_PER_IP
            )
        except Exception as error:
            logging.getLogger(__name__).error("login rate limit check failed: %s", error)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Login is temporarily unavailable. Please try again shortly.",
            ) from error
        if new_count is None:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts from this address. Try again later.",
            )

    @app.post("/v1/auth/login", dependencies=[Depends(require_login_rate_limit)])
    def login(payload: LoginCreate, response: Response) -> dict[str, Any]:
        user = research_service.store.get_user_by_email(payload.email)
        if user is None or not auth.verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        token = auth.create_access_token(user_id=user["id"], email=user["email"], token_version=user["token_version"])
        _set_session_cookie(response, token)
        csrf_token = auth.generate_csrf_token(user_id=user["id"], token_version=user["token_version"])
        return _envelope({"token": token, "csrf_token": csrf_token, "email": user["email"], "tier": user["tier"]})

    @app.post("/v1/auth/logout")
    def logout(request: Request, response: Response) -> dict[str, Any]:
        # Best-effort revocation: if the presented session is still valid,
        # bump token_version to invalidate every JWT issued for this account
        # (not just the one used to log out — a real session kill, not just
        # clearing this one browser's cookies). But cookies must always be
        # cleared, even for an already-expired/invalid session — a user
        # clicking "log out" on a stale tab should never be left with dead
        # cookies just because the session died first. A valid session still
        # must present a correct CSRF token to actually trigger the
        # revocation+cookie-clear, same protection every other mutating
        # cookie-authenticated route gets via require_csrf.
        try:
            user = get_current_user(request)
        except HTTPException:
            user = None
        if user is not None:
            _verify_csrf(request, user)
            research_service.store.bump_token_version(user["id"])
        response.delete_cookie("pit_session", secure=True, samesite="none")
        return _envelope({"logged_out": True})

    @app.get("/v1/auth/me")
    def get_me(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        plan = auth.PLANS.get(user["tier"], auth.PLANS["free"])
        period = auth.current_period()
        used = research_service.store.get_usage(user_id=user["id"], period=period)
        csrf_token = auth.generate_csrf_token(user_id=user["id"], token_version=user["token_version"])
        return _envelope({
            "email": user["email"],
            "tier": user["tier"],
            "csrf_token": csrf_token,
            "email_verified": bool(user["email_verified"]),
            "tier_expires_at": user["tier_expires_at"],
            "usage": {"used": used, "limit": plan["monthly_limit"], "period": period},
        })

    @app.post("/v1/admin/set-tier", dependencies=[Depends(require_admin)])
    def set_tier(payload: SetTierCreate) -> dict[str, Any]:
        user = research_service.store.get_user_by_email(payload.email)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
        if payload.tier == "free":
            expires_at = None
        else:
            duration_days = payload.expires_in_days or auth.DEFAULT_TIER_DURATION_DAYS.get(payload.tier, 30)
            expires_at = (datetime.now(UTC) + timedelta(days=duration_days)).isoformat()
        updated = research_service.store.set_user_tier(user["id"], payload.tier, expires_at=expires_at)
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
        return _envelope({"email": updated["email"], "tier": updated["tier"], "tier_expires_at": updated["tier_expires_at"]})

    @app.post("/v1/research-runs", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
    def create_research_run(payload: ResearchRunCreate, user: dict[str, Any] = Depends(require_quota)) -> dict[str, Any]:
        try:
            run = research_service.run_science_research(
                user_id=user["id"],
                query=payload.query,
                target_market=payload.target_market,
                application=payload.application,
                cutoff_at=datetime.now(UTC).isoformat(),
                from_publication_date=payload.from_publication_date,
                limit=payload.limit,
            )
        except ResearchExecutionError as error:
            _handle_research_error(error)
        return _envelope(run)

    @app.post("/v1/research-runs/full", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
    def create_full_research_run(payload: ResearchRunFullCreate, user: dict[str, Any] = Depends(require_quota)) -> dict[str, Any]:
        try:
            run = research_service.run_full_pipeline(
                user_id=user["id"],
                query=payload.query,
                target_market=payload.target_market,
                application=payload.application,
                cutoff_at=datetime.now(UTC).isoformat(),
                from_publication_date=payload.from_publication_date,
                limit=payload.limit,
                hs_code=payload.hs_code,
            )
        except ResearchExecutionError as error:
            _handle_research_error(error)
        return _envelope(run)

    @app.get("/v1/research-runs/{run_id}")
    async def get_research_run(run_id: str, user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        try:
            run = research_service.store.get_run_detail(run_id)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
        _check_run_ownership(run, user)
        return _envelope(run)

    @app.post("/v1/research-runs/{run_id}/enrich/{domain}", dependencies=[Depends(require_csrf)])
    def enrich_research_run(
        run_id: str,
        domain: str,
        payload: DomainEnrichmentCreate,
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        handler_name = ENRICHMENT_HANDLERS.get(domain)
        if handler_name is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"unknown enrichment domain: {domain}")
        try:
            existing_run = research_service.store.get_run(run_id)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
        _check_run_ownership(existing_run, user)
        handler = getattr(research_service, handler_name)
        try:
            if domain == "trade":
                run = handler(run_id=run_id, limit=payload.limit, hs_code=payload.hs_code)
            else:
                run = handler(run_id=run_id, limit=payload.limit)
        except RuntimeError as error:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
        except ResearchExecutionError as error:
            _handle_research_error(error)
        return _envelope(run)

    @app.get("/v1/research-runs/{run_id}/report")
    async def get_research_report(run_id: str, user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        try:
            existing_run = research_service.store.get_run(run_id)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
        _check_run_ownership(existing_run, user)
        run = research_service.store.get_run_detail(run_id)
        scores = scoring_svc.calculate_scores(run_id)
        domain_scores = scoring_svc.build_domain_scores(run_id)
        report = report_gen.generate_json(run=run, scores=scores, domain_scores=domain_scores)
        return {
            "data": report,
            "meta": {"confidence": "ok", "evidence_count": len(run.get("evidence", []))},
            "trace": {"version": "0.1.0", "timestamp": datetime.now(UTC).isoformat()},
        }

    @app.get("/v1/research-runs/{run_id}/report.pdf")
    async def get_research_report_pdf(run_id: str, user: dict[str, Any] = Depends(get_current_user)) -> Response:
        try:
            existing_run = research_service.store.get_run(run_id)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
        _check_run_ownership(existing_run, user)
        run = research_service.store.get_run_detail(run_id)
        scores = scoring_svc.calculate_scores(run_id)
        domain_scores = scoring_svc.build_domain_scores(run_id)
        pdf_bytes = report_gen.generate_pdf(run=run, scores=scores, domain_scores=domain_scores)
        return Response(content=pdf_bytes, media_type="application/pdf")

    @app.get("/v1/agents/status")
    def get_agents_status() -> dict[str, Any]:
        try:
            from pit_agents.product_intelligence.ficha_service import (
                agents_status as _agents_status,
            )
        except ImportError:
            return {
                "data": {
                    "ficha_available": False,
                    "reason": 'Modulo de agentes no encontrado. Instala: pip install -e ".[agents]"',
                    "anthropic_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
                }
            }
        return {"data": _agents_status()}

    @app.post("/v1/research-runs/{run_id}/ficha", dependencies=[Depends(require_csrf)])
    async def generate_opportunity_ficha(
        run_id: str,
        payload: FichaCreate,
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        try:
            run_row = research_service.store.get_run(run_id)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
        _check_run_ownership(run_row, user)

        try:
            from pit_agents.product_intelligence.ficha_service import (
                agents_dependencies_ready,
                generate_dossier_for_run,
            )
        except ImportError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='Modulo de agentes no instalado. Ejecuta: pip install -e ".[agents]"',
            ) from error

        ready, reason = agents_dependencies_ready()
        if not ready:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=reason)

        run = research_service.store.get_run_detail(run_id)
        scores = scoring_svc.calculate_scores(run_id)
        domain_scores = scoring_svc.build_domain_scores(run_id)
        report = report_gen.generate_json(run=run, scores=scores, domain_scores=domain_scores)

        try:
            result = await generate_dossier_for_run(
                run_id=run_id,
                report=report,
                query=run_row["query_original"],
                target_market=run_row["target_market"],
                segment=payload.segment,
                stage=payload.stage,
                market_label=payload.market_label,
            )
        except RuntimeError as error:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
        except Exception as error:
            logger.exception("ficha_generation_failed", extra={"run_id": run_id})
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error generando ficha: {error}",
            ) from error

        return {
            "data": result,
            "meta": {
                "confidence": "ok",
                "pit_run_id": run_id,
            },
            "trace": {
                "version": "0.1.0",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        }

    @app.get("/v1/connectors/status", dependencies=[Depends(require_admin)])
    async def connectors_status() -> dict[str, Any]:
        stats_rows = research_service.store.get_connector_stats()
        freshness_rows = research_service.store.get_freshness()
        quota_rows = research_service.store.get_quota_usage()
        stats = {row["source"]: {"total_requests": row["total_requests"], "completed": row["completed"], "failed": row["failed"], "success_rate": row["success_rate"]} for row in stats_rows}
        freshness = {row["source"]: {"last_fetched": row["last_fetched"], "total": row["total"]} for row in freshness_rows}
        quota = {row["source"]: {"request_count": row["request_count"], "rate_limited": row["rate_limited"]} for row in quota_rows}
        metrics = {row["source"]: {"requests": row["total_requests"], "errors": row["failed"]} for row in stats_rows}
        return {"stats": stats, "freshness": freshness, "quota": quota, "metrics": metrics}

    @app.get("/metrics", dependencies=[Depends(require_admin)])
    async def metrics() -> dict[str, Any]:
        return _metrics.to_dict()

    if ASSETS_DIR.is_dir():
        app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")
    if WEB_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="frontend")

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("pit.api:app", host="127.0.0.1", port=8000, reload=False)
