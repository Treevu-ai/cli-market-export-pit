"""FastAPI entry point for PIT research runs."""

from __future__ import annotations

import json
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any

def _load_env_file() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


_load_env_file()

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

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
    )
    return service, ScoringService(store), ReportGenerator()


_API_KEY = os.getenv("PIT_API_KEY")
_ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("PIT_CORS_ORIGINS", "").split(",") if origin.strip()]


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
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


class APIKeyMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        api_key = os.getenv("PIT_API_KEY")
        if api_key:
            headers = {key.decode().lower(): value.decode() for key, value in scope.get("headers", [])}
            request_api_key = headers.get("x-api-key")
            if request_api_key is None or not secrets.compare_digest(request_api_key, api_key):
                from starlette.responses import JSONResponse
                response = JSONResponse({"detail": "Invalid API key"}, status_code=401)
                await response(scope, receive, send)
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


def _handle_research_error(error: ResearchExecutionError) -> None:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={"research_run_id": error.run_id, "message": error.message},
    ) from error


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
    app.add_middleware(APIKeyMiddleware)
    if _ALLOWED_ORIGINS:
        from starlette.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=_ALLOWED_ORIGINS,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    _setup_logging()

    @app.get("/v1/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok", "version": "0.1.0"}

    @app.post("/v1/research-runs", status_code=status.HTTP_201_CREATED)
    def create_research_run(payload: ResearchRunCreate) -> dict[str, Any]:
        try:
            run = research_service.run_science_research(
                query=payload.query,
                target_market=payload.target_market,
                application=payload.application,
                cutoff_at=datetime.now(timezone.utc).isoformat(),
                from_publication_date=payload.from_publication_date,
                limit=payload.limit,
            )
        except ResearchExecutionError as error:
            _handle_research_error(error)
        return _envelope(run)

    @app.post("/v1/research-runs/full", status_code=status.HTTP_201_CREATED)
    def create_full_research_run(payload: ResearchRunFullCreate) -> dict[str, Any]:
        try:
            run = research_service.run_full_pipeline(
                query=payload.query,
                target_market=payload.target_market,
                application=payload.application,
                cutoff_at=datetime.now(timezone.utc).isoformat(),
                from_publication_date=payload.from_publication_date,
                limit=payload.limit,
                hs_code=payload.hs_code,
            )
        except ResearchExecutionError as error:
            _handle_research_error(error)
        return _envelope(run)

    @app.get("/v1/research-runs/{run_id}")
    async def get_research_run(run_id: str) -> dict[str, Any]:
        try:
            run = research_service.store.get_run_detail(run_id)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
        return _envelope(run)

    @app.post("/v1/research-runs/{run_id}/enrich/{domain}")
    def enrich_research_run(run_id: str, domain: str, payload: DomainEnrichmentCreate) -> dict[str, Any]:
        handler_name = ENRICHMENT_HANDLERS.get(domain)
        if handler_name is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"unknown enrichment domain: {domain}")
        try:
            research_service.store.get_run(run_id)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
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
    async def get_research_report(run_id: str) -> dict[str, Any]:
        try:
            research_service.store.get_run(run_id)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
        run = research_service.store.get_run_detail(run_id)
        scores = scoring_svc.calculate_scores(run_id)
        domain_scores = scoring_svc.build_domain_scores(run_id)
        report = report_gen.generate_json(run=run, scores=scores, domain_scores=domain_scores)
        return {
            "data": report,
            "meta": {"confidence": "ok", "evidence_count": len(run.get("evidence", []))},
            "trace": {"version": "0.1.0", "timestamp": datetime.now(timezone.utc).isoformat()},
        }

    @app.get("/v1/research-runs/{run_id}/report.pdf")
    async def get_research_report_pdf(run_id: str) -> Response:
        try:
            research_service.store.get_run(run_id)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
        run = research_service.store.get_run_detail(run_id)
        scores = scoring_svc.calculate_scores(run_id)
        domain_scores = scoring_svc.build_domain_scores(run_id)
        pdf_bytes = report_gen.generate_pdf(run=run, scores=scores, domain_scores=domain_scores)
        return Response(content=pdf_bytes, media_type="application/pdf")

    @app.get("/v1/agents/status")
    def get_agents_status() -> dict[str, Any]:
        try:
            from pit_agents.product_intelligence.ficha_service import agents_status as _agents_status
        except ImportError:
            return {
                "data": {
                    "ficha_available": False,
                    "reason": 'Modulo de agentes no encontrado. Instala: pip install -e ".[agents]"',
                    "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
                }
            }
        return {"data": _agents_status()}

    @app.post("/v1/research-runs/{run_id}/ficha")
    async def generate_opportunity_ficha(run_id: str, payload: FichaCreate) -> dict[str, Any]:
        try:
            run_row = research_service.store.get_run(run_id)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")

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
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

    @app.get("/v1/connectors/status")
    async def connectors_status() -> dict[str, Any]:
        stats_rows = research_service.store.get_connector_stats()
        freshness_rows = research_service.store.get_freshness()
        quota_rows = research_service.store.get_quota_usage()
        stats = {row["source"]: {"total_requests": row["total_requests"], "completed": row["completed"], "failed": row["failed"], "success_rate": row["success_rate"]} for row in stats_rows}
        freshness = {row["source"]: {"last_fetched": row["last_fetched"], "total": row["total"]} for row in freshness_rows}
        quota = {row["source"]: {"request_count": row["request_count"], "rate_limited": row["rate_limited"]} for row in quota_rows}
        metrics = {row["source"]: {"requests": row["total_requests"], "errors": row["failed"]} for row in stats_rows}
        return {"stats": stats, "freshness": freshness, "quota": quota, "metrics": metrics}

    @app.get("/metrics")
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
