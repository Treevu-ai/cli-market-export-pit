"""USDA FAS (Foreign Agricultural Service) PSD connector for global supply/demand context."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class USDAFASRequestError(RuntimeError):
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
class USDAFASResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class USDAFASConnector:
    source = "usda_fas"
    license_name = "USDA FAS PSD; US government public domain data"
    base_url = "https://api.fas.usda.gov/api/psd"

    # Confirmed live against /api/psd/commodities: USDA's PSD database
    # tracks ~55 bulk agricultural commodities (grains, oilseeds, dairy,
    # meat, a handful of fresh fruits) -- not the specialty/functional
    # crops that make up most of PIT's product catalog. Only query terms
    # that genuinely match a PSD commodity get a request; everything else
    # is skipped rather than guessing a code.
    COMMODITY_CODES: dict[str, str] = {
        "cafe": "0711100",
        "café": "0711100",
        "coffee": "0711100",
        "uva": "0575100",
        "grape": "0575100",
        "grapes": "0575100",
        "limon": "0572120",
        "limón": "0572120",
        "lemon": "0572120",
        "lime": "0572120",
    }
    # Generic attribute IDs confirmed live to appear consistently across
    # commodities (coffee, grapes): 28=Production, 86=Total Supply,
    # 88=Exports, 125=Domestic Consumption, 176=Ending Stocks. Commodity-
    # specific sub-splits (e.g. coffee's Arabica/Robusta breakdown) exist
    # too but aren't consistent across commodities, so only the generic
    # set is surfaced.
    ATTRIBUTE_NAMES: dict[int, str] = {
        28: "production",
        86: "total_supply",
        88: "exports",
        125: "domestic_consumption",
        176: "ending_stocks",
    }

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def _match_commodity_code(self, query: str) -> str | None:
        normalized = query.lower()
        for keyword, code in self.COMMODITY_CODES.items():
            if keyword in normalized:
                return code
        return None

    def search(self, *, query: str, market_year: str) -> USDAFASResponse:
        if not self.api_key:
            return USDAFASResponse(
                request_url=self.base_url,
                request_params={"query": query, "market_year": market_year},
                http_status=200,
                raw_content=b"[]",
                works=[],
            )
        commodity_code = self._match_commodity_code(query)
        if commodity_code is None:
            return USDAFASResponse(
                request_url=self.base_url,
                request_params={"query": query, "market_year": market_year},
                http_status=200,
                raw_content=b"[]",
                works=[],
            )

        request_url = f"{self.base_url}/commodity/{commodity_code}/world/year/{market_year}"
        params = {"commodity_code": commodity_code, "market_year": market_year}
        request = Request(request_url, headers={"X-Api-Key": self.api_key, "Accept": "application/json"})
        try:
            with urlopen(request, timeout=20) as response:
                raw_content = response.read()
                http_status = response.status
        except HTTPError as error:
            raw_content = error.read()
            # Confirmed live: USDA FAS returns HTTP 404 with an empty body
            # for a market year with no PSD data yet -- a normal "not
            # published yet" answer, not a request failure.
            if error.code == 404:
                return USDAFASResponse(
                    request_url=request_url,
                    request_params=params,
                    http_status=200,
                    raw_content=raw_content,
                    works=[],
                )
            raise USDAFASRequestError(
                f"USDA FAS returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error
        except URLError as error:
            raise USDAFASRequestError(
                f"USDA FAS network error: {error.reason}",
                request_url=request_url,
                request_params=params,
            ) from error

        try:
            rows = json.loads(raw_content)
        except json.JSONDecodeError as error:
            raise USDAFASRequestError(
                "USDA FAS response was not valid JSON",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error

        works: list[dict[str, Any]] = []
        for row in rows:
            attribute_name = self.ATTRIBUTE_NAMES.get(row.get("attributeId"))
            if attribute_name is None:
                continue
            works.append({
                "commodity_code": row.get("commodityCode"),
                "market_year": row.get("marketYear"),
                "attribute": attribute_name,
                "value": row.get("value"),
                "unit_id": row.get("unitId"),
                "source": "usda_fas",
            })

        return USDAFASResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )
