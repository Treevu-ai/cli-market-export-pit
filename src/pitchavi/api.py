"""FastAPI entry point for Pitchavi research runs."""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path as ApiPath, Request, status
from pydantic import BaseModel, Field

from .comtrade import ComtradeConnector
from .cordis import CORDISConnector
from .crossref import CrossrefConnector
from .epo_ops import EPOOPSConnector
from .gdelt import GDELTConnector
from .nih_reporter import NIHReporterConnector
from .nsf_awards import NSFAwardsConnector
from .openalex import OpenAlexConnector
from .openfda import OpenFDAConnector
from .efsa_eurlex import EFSALexConnector
from .fooddata_central import FoodDataCentralConnector
from .climatiq import ClimatiqConnector
from .pubmed import PubMedConnector
from .reports import ReportGenerator
from .research import ResearchExecutionError, ResearchService, ScoringService
from .semanticscholar import SemanticScholarConnector
from .storage import ResearchStore

logger = logging.getLogger("pitchavi")


class ResearchRunCreate(BaseModel):
    query: Annotated[str, Field(min_length=3, max_length=300)]
    target_market: Annotated[str, Field(pattern=r"^[A-Z]{2}$")] = "US"
    application: Annotated[str, Field(min_length=3, max_length=200)] = "functional foods and beverages"
    from_publication_date: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")] = "2021-01-01"
    limit: Annotated[int, Field(ge=1, le=100)] = 25


class CrossrefEnrichmentCreate(BaseModel):
    limit: Annotated[int, Field(ge=1, le=100)] = 25


class DomainEnrichmentCreate(BaseModel):
    limit: Annotated[int, Field(ge=1, le=100)] = 25


def _default_service() -> ResearchService:
    database_path = Path(os.getenv("PITCHAVI_DB_PATH", "data/pitchavi.db"))
    raw_directory = Path(os.getenv("PITCHAVI_RAW_DIR", "data/raw"))
    patent_connector = None
    if os.getenv("EPO_OPS_CONSUMER_KEY") and os.getenv("EPO_OPS_CONSUMER_SECRET"):
        patent_connector = EPOOPSConnector(
            os.getenv("EPO_OPS_CONSUMER_KEY", ""),
            os.getenv("EPO_OPS_CONSUMER_SECRET", ""),
        )
    trend_connector = GDELTConnector()
    trade_connector = ComtradeConnector()
    cordis_connector = CORDISConnector()
    nih_connector = NIHReporterConnector()
    nsf_connector = NSFAwardsConnector()
    openfda_connector = OpenFDAConnector()
    efsa_connector = EFSALexConnector()
    fooddata_connector = FoodDataCentralConnector(api_key=os.getenv("FOODDATA_CENTRAL_API_KEY"))
    climatiq_connector = ClimatiqConnector(api_key=os.getenv("CLIMATIQ_API_KEY"))
    store = ResearchStore(database_path, raw_directory)
    return ResearchService(
        store,
        OpenAlexConnector(),
        CrossrefConnector(os.getenv("PITCHAVI_CONTACT_EMAIL")),
        PubMedConnector(),
        SemanticScholarConnector(),
        patent_connector,
        trend_connector,
        trade_connector,
        cordis_connector,
        nih_connector,
        nsf_connector,
        openfda_connector,
        efsa_connector,
        fooddata_connector,
        climatiq_connector,
    ), ScoringService(store), ReportGenerator()


_API_KEY = os.getenv("PITCHAVI_API_KEY")
_ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("PITCHAVI_CORS_ORIGINS", "").split(",") if origin.strip()]


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
        api_key = os.getenv("PITCHAVI_API_KEY")
        if api_key:
            headers = {key.decode().lower(): value.decode() for key, value in scope.get("headers", [])}
            request_api_key = headers.get("x-api-key")
            if request_api_key != api_key:
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


def create_app(service: ResearchService | None = None, scoring_service: ScoringService | None = None, report_generator: ReportGenerator | None = None) -> FastAPI:
    research_service = service or _default_service()[0]
    scoring_svc = scoring_service or _default_service()[1]
    report_gen = report_generator or _default_service()[2]
    app = FastAPI(
        title="Pitchavi Research API",
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
    def health_check() -> dict:
        return {"status": "ok", "version": "0.1.0"}

    @app.post("/v1/research-runs", status_code=status.HTTP_201_CREATED)
    def create_research_run(payload: ResearchRunCreate) -> dict:
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
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"research_run_id": error.run_id, "message": error.message},
            ) from error
        return _envelope(run)

    @app.get("/v1/research-runs/{run_id}")
    async def get_research_run(run_id: str) -> dict[str, Any]:
        try:
            run = research_service.store.get_run_detail(run_id)
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
        return _envelope(run)

    @app.get("/v1/research-runs/{run_id}/report")
    async def get_research_report(run_id: str) -> dict[str, Any]:
        run = research_service.store.get_run(run_id)
        if not run:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
        scores = scoring_svc.calculate_scores(run_id)
        weights = {"science": 0.30, "patent": 0.20, "trend": 0.20, "trade": 0.30}
        domain_scores = []
        for domain, payloads in research_service.store.get_domain_summaries(run_id).items():
            payload = next(iter(payloads.values()), {}) if payloads else {}
            score = scoring_svc._estimate_score(domain, payload)
            confidence = "high" if scoring_svc._estimate_coverage(domain, payload) > 0.7 else "medium"
            domain_scores.append({
                "domain": domain,
                "score": score,
                "confidence": confidence,
                "weight": weights.get(domain, 0.0),
                "coverage": scoring_svc._estimate_coverage(domain, payload),
            })
        report = report_gen.generate_json(run=run, scores=scores, domain_scores=domain_scores)
        return {
            "data": report,
            "meta": {"confidence": "ok", "evidence_count": len(run.get("evidence", []))},
            "trace": {"version": "0.1.0", "timestamp": datetime.now(timezone.utc).isoformat()},
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

        return {
            "stats": stats,
            "freshness": freshness,
            "quota": quota,
            "metrics": metrics,
        }

    @app.get("/metrics")
    async def metrics() -> dict[str, Any]:
        return _metrics.to_dict()

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("pitchavi.api:app", host="127.0.0.1", port=8000, reload=False)
