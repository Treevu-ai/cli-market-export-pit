"""UN Comtrade connector for trade flows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ISO_TO_COMTRADE: dict[str, str] = {
    "US": "842",
    "DE": "276",
    "PE": "604",
    "GB": "826",
    "FR": "250",
    "ES": "724",
    "IT": "380",
    "MX": "484",
    "BR": "076",
    "CN": "156",
    "JP": "392",
}


class ComtradeRequestError(RuntimeError):
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
class ComtradeResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class ComtradeConnector:
    source = "comtrade"
    license_name = "UN Comtrade; open data with attribution"
    base_url = "https://comtradeapi.un.org/getData"

    def search(
        self,
        *,
        query: str,
        from_publication_date: str,
        limit: int,
        hs_code: str | None = None,
        reporter_country: str = "0",
        partner_country: str | None = None,
        target_market: str | None = None,
        flow: str = "all",
    ) -> ComtradeResponse:
        resolved_partner = partner_country
        if resolved_partner is None and target_market:
            resolved_partner = ISO_TO_COMTRADE.get(target_market.upper(), "0")
        if resolved_partner is None:
            resolved_partner = "0"
        params: dict[str, str] = {
            "subscription-key": "public",
            "filter": json.dumps({
                "reporterCode": reporter_country,
                "partnerCode": resolved_partner,
                "period": f"{from_publication_date[:4]}-2025",
                "cmdCode": hs_code or "",
                "flow": flow,
            }),
            "page": "1",
            "perPage": str(limit),
        }
        request_url = f"{self.base_url}?{urlencode(params)}"
        request = Request(
            request_url,
            headers={"User-Agent": "Pitchavi/0.1 research-service"},
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw_content = response.read()
                http_status = response.status
        except HTTPError as error:
            raw_content = error.read()
            raise ComtradeRequestError(
                f"UN Comtrade returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error
        except URLError as error:
            raise ComtradeRequestError(
                f"UN Comtrade network error: {error.reason}",
                request_url=request_url,
                request_params=params,
            ) from error

        try:
            body = json.loads(raw_content)
            records = body.get("data", [])
        except (json.JSONDecodeError, AttributeError, TypeError) as error:
            raise ComtradeRequestError(
                "UN Comtrade response did not contain data",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error

        works: list[dict[str, Any]] = []
        for record in records:
            trade_value = record.get("tradeValue")
            net_weight = record.get("netWeight")
            period = record.get("period")
            works.append({
                "reporter": record.get("reporterDesc"),
                "partner": record.get("partnerDesc"),
                "flow": record.get("flowDesc"),
                "period": str(period) if period else None,
                "trade_value_usd": trade_value,
                "net_weight_kg": net_weight,
                "hs_code": record.get("cmdCode"),
                "source": "comtrade",
            })

        return ComtradeResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )
