"""BCRP (Banco Central de Reserva del Perú) connector for macro time series."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class BCRPRequestError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        http_status: int | None = None,
        raw_content: bytes | None = None,
        request_url: str | None = None,
        request_params: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.http_status = http_status
        self.raw_content = raw_content
        self.request_url = request_url
        self.request_params = request_params


@dataclass(frozen=True)
class BCRPResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


def _shift_period(now: datetime, months_back: int) -> tuple[int, int]:
    total_months = now.year * 12 + (now.month - 1) - months_back
    return total_months // 12, total_months % 12 + 1


class BCRPConnector:
    source = "bcrp"
    license_name = "BCRP public statistics API; no auth required"
    base_url = "https://estadisticas.bcrp.gob.pe"

    # Verified live against estadisticas.bcrp.gob.pe: "Tipo de cambio - promedio
    # del periodo (S/ por US$)". Other series codes are not hardcoded here until
    # manually verified — BCRP returns a WAF/HTML page (not a clean error) for
    # unrecognized codes.
    DEFAULT_SERIES: ClassVar[list[str]] = ["PN01207PM"]

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("BCRP_API_URL") or self.base_url).rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": "PIT/0.1 research-service",
            "Accept": "application/json",
        }

    def search(
        self,
        *,
        series_codes: list[str] | None = None,
        months_back: int = 12,
        language: str = "esp",
    ) -> BCRPResponse:
        codes = series_codes or self.DEFAULT_SERIES
        now = datetime.now(UTC)
        start_year, start_month = _shift_period(now, months_back)
        end_year, end_month = _shift_period(now, 0)
        start_period = f"{start_year}-{start_month}"
        end_period = f"{end_year}-{end_month}"
        path = f"/estadisticas/series/api/{'-'.join(codes)}/json/{start_period}/{end_period}/{language}"
        request_url = f"{self.base_url}{path}"
        request_params = {
            "series_codes": codes,
            "start_period": start_period,
            "end_period": end_period,
            "language": language,
        }
        request = Request(request_url, headers=self._headers(), method="GET")
        try:
            with urlopen(request, timeout=45) as response:
                raw_content = response.read()
                http_status = response.status
        except HTTPError as error:
            raw_content = error.read()
            raise BCRPRequestError(
                f"BCRP returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=request_params,
            ) from error
        except URLError as error:
            raise BCRPRequestError(
                f"BCRP network error: {error.reason}",
                request_url=request_url,
                request_params=request_params,
            ) from error
        try:
            payload = json.loads(raw_content)
        except json.JSONDecodeError as error:
            raise BCRPRequestError(
                "BCRP returned invalid JSON (unrecognized series code or WAF block)",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=request_params,
            ) from error
        if not isinstance(payload, dict):
            raise BCRPRequestError(
                "BCRP response was not a JSON object",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=request_params,
            )
        works = self._normalize(payload, codes)
        return BCRPResponse(
            request_url=request_url,
            request_params=request_params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )

    def _normalize(self, payload: dict[str, Any], codes: list[str]) -> list[dict[str, Any]]:
        works: list[dict[str, Any]] = []
        series_list = payload.get("config", {}).get("series", []) or []
        periods = payload.get("periods", []) or []
        for series_index, series in enumerate(series_list):
            series_name = str(series.get("name") or "").strip()
            series_code = codes[series_index] if series_index < len(codes) else series_name
            if not series_name:
                continue
            for period in periods:
                period_name = str(period.get("name") or "").strip()
                values = period.get("values") or []
                if not period_name or series_index >= len(values):
                    continue
                value = values[series_index]
                works.append({
                    "external_id": f"bcrp:{series_code}:{period_name}",
                    "title": f"{series_name} — {period_name}",
                    "series_code": series_code,
                    "series_name": series_name,
                    "period": period_name,
                    "value": value,
                    "source": "bcrp",
                })
        return works
