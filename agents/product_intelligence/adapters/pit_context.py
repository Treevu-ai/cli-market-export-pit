"""Fetch PIT research reports and map them to agent context snapshots."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SCIENTIFIC_KEYS = frozenset({
    "openalex_aggregation",
    "epo_ops_aggregation",
    "crossref_aggregation",
    "pubmed_aggregation",
    "semanticscholar_aggregation",
})

MARKET_KEYS = frozenset({
    "climarket_aggregation",
    "comtrade_aggregation",
    "gdelt_aggregation",
})

REGULATORY_KEYS = frozenset({
    "regulatory_aggregation",
})


@dataclass(frozen=True)
class PITContextBundle:
    run_id: str
    report: dict[str, Any]
    scientific: dict[str, Any]
    market: dict[str, Any]
    regulatory: dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(
            {
                "run_id": self.run_id,
                "scientific": self.scientific,
                "market": self.market,
                "regulatory": self.regulatory,
            },
            ensure_ascii=False,
            indent=2,
        )


def build_context_bundle(*, run_id: str, report: dict[str, Any]) -> PITContextBundle:
    """Map a PIT JSON report into the three snapshots expected by agent tools."""
    evidence = report.get("evidence_summary") or {}
    score = report.get("score") or {}
    meta = {
        "run_id": run_id,
        "query": report.get("query"),
        "target_market": report.get("target_market"),
        "application": report.get("application"),
        "cutoff_at": report.get("cutoff_at"),
        "pit_recommendation": score.get("recommendation"),
        "pit_opportunity_score": score.get("opportunity_score"),
        "pit_coverage_factor": score.get("coverage_factor"),
        "pit_dimensions": score.get("dimensions"),
        "claims": report.get("claims") or [],
        "sources": report.get("sources") or [],
    }

    scientific = {**meta, "aggregations": {key: evidence[key] for key in SCIENTIFIC_KEYS if key in evidence}}
    market = {**meta, "aggregations": {key: evidence[key] for key in MARKET_KEYS if key in evidence}}
    regulatory = {**meta, "aggregations": {key: evidence[key] for key in REGULATORY_KEYS if key in evidence}}

    for label, bucket, keys in (
        ("scientific", scientific, SCIENTIFIC_KEYS),
        ("market", market, MARKET_KEYS),
        ("regulatory", regulatory, REGULATORY_KEYS),
    ):
        missing = sorted(keys - set(bucket["aggregations"]))
        if missing:
            bucket["vacios_criticos"] = bucket.get("vacios_criticos", []) + [
                f"Sin agregación PIT: {', '.join(missing)}"
            ]
        if not bucket["aggregations"]:
            bucket["status"] = "insufficient_evidence"
            bucket["message"] = f"PIT no devolvió evidencia {label} para este run."
        else:
            bucket["status"] = "ok"

    return PITContextBundle(
        run_id=run_id,
        report=report,
        scientific=scientific,
        market=market,
        regulatory=regulatory,
    )


class PITClient:
    """Minimal HTTP client for the PIT research API."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        api_key: str | None = None,
        timeout: float = 180.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("PIT_API_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.api_key = api_key or os.getenv("PIT_API_KEY")
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "PIT-product-intelligence/0.1",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def _request_json(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=data,
            headers=self._headers(),
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"PIT API {error.code} {path}: {detail}") from error
        except URLError as error:
            raise RuntimeError(f"PIT API unreachable at {self.base_url}{path}: {error}") from error
        if not isinstance(payload, dict):
            raise RuntimeError(f"PIT API returned non-object JSON for {path}")
        return payload

    def create_full_run(
        self,
        *,
        query: str,
        target_market: str = "US",
        application: str = "functional foods and beverages",
        from_publication_date: str = "2021-01-01",
        limit: int = 25,
        hs_code: str | None = None,
    ) -> str:
        body: dict[str, Any] = {
            "query": query,
            "target_market": target_market,
            "application": application,
            "from_publication_date": from_publication_date,
            "limit": limit,
        }
        if hs_code:
            body["hs_code"] = hs_code
        envelope = self._request_json("POST", "/v1/research-runs/full", body)
        run = envelope.get("data") or {}
        run_id = run.get("id")
        if not run_id:
            raise RuntimeError("PIT API did not return a research run id")
        return run_id

    def get_report(self, run_id: str) -> dict[str, Any]:
        envelope = self._request_json("GET", f"/v1/research-runs/{run_id}/report")
        report = envelope.get("data")
        if not isinstance(report, dict):
            raise RuntimeError(f"PIT report for {run_id} is missing or invalid")
        return report

    def fetch_context_bundle(
        self,
        *,
        query: str,
        target_market: str = "US",
        application: str = "functional foods and beverages",
        from_publication_date: str = "2021-01-01",
        limit: int = 25,
        hs_code: str | None = None,
    ) -> PITContextBundle:
        run_id = self.create_full_run(
            query=query,
            target_market=target_market,
            application=application,
            from_publication_date=from_publication_date,
            limit=limit,
            hs_code=hs_code,
        )
        report = self.get_report(run_id)
        return build_context_bundle(run_id=run_id, report=report)

    def context_bundle_for_run(self, run_id: str) -> PITContextBundle:
        report = self.get_report(run_id)
        return build_context_bundle(run_id=run_id, report=report)
