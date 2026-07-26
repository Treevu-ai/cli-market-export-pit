"""CLI Market connector for shelf prices and market intelligence."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class CLIMarketRequestError(RuntimeError):
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
class CLIMarketResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


DEFAULT_LINE = "supermercados"


class CLIMarketConnector:
    source = "cli_market"
    license_name = "CLI Market shelf data; attribution required"
    base_url = "https://cli-market-api.fly.dev"

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or os.getenv("CLIMARKET_API_KEY") or os.getenv("MARKET_API_KEY")
        self.base_url = (base_url or os.getenv("CLIMARKET_API_URL") or os.getenv("MARKET_API_URL") or self.base_url).rstrip("/")

    def _headers(self) -> dict[str, str]:
        headers = {
            "User-Agent": "PIT/0.1 research-service",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> tuple[str, dict[str, Any], int, bytes]:
        request_url = f"{self.base_url}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        if method == "GET" and params:
            query = {key: str(value) for key, value in params.items() if value is not None}
            if query:
                request_url = f"{request_url}?{urlencode(query)}"
        request = Request(request_url, data=data, headers=self._headers(), method=method)
        try:
            with urlopen(request, timeout=45) as response:
                raw_content = response.read()
                http_status = response.status
        except HTTPError as error:
            raw_content = error.read()
            raise CLIMarketRequestError(
                f"CLI Market returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params or body or {},
            ) from error
        except URLError as error:
            raise CLIMarketRequestError(
                f"CLI Market network error: {error.reason}",
                request_url=request_url,
                request_params=params or body or {},
            ) from error
        try:
            payload = json.loads(raw_content)
        except json.JSONDecodeError as error:
            raise CLIMarketRequestError(
                "CLI Market returned invalid JSON",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params or body or {},
            ) from error
        if not isinstance(payload, dict):
            raise CLIMarketRequestError(
                "CLI Market response was not a JSON object",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params or body or {},
            )
        return request_url, payload, http_status, raw_content

    def compare_products(
        self,
        *,
        query: str,
        country: str,
        line: str = DEFAULT_LINE,
        limit: int = 10,
    ) -> CLIMarketResponse:
        body = {"query": query, "country": country, "line": line, "limit": limit, "require_all": False}
        request_url, payload, http_status, raw_content = self._request_json(
            method="POST",
            path="/products/compare",
            body=body,
        )
        works = self._normalize_compare(payload)
        return CLIMarketResponse(
            request_url=request_url,
            request_params=body,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )

    def search_products(
        self,
        *,
        query: str,
        country: str,
        line: str = DEFAULT_LINE,
        limit: int = 10,
    ) -> CLIMarketResponse:
        body = {"query": query, "country": country, "line": line, "limit": limit, "require_all": False}
        request_url, payload, http_status, raw_content = self._request_json(
            method="POST",
            path="/products/search",
            body=body,
        )
        works = self._normalize_search(payload)
        return CLIMarketResponse(
            request_url=request_url,
            request_params=body,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )

    def intel_brief(
        self,
        *,
        country: str,
        line: str = DEFAULT_LINE,
        days: int = 7,
    ) -> CLIMarketResponse:
        params = {"country": country, "line": line, "days": str(days)}
        request_url, payload, http_status, raw_content = self._request_json(
            method="GET",
            path="/v1/intel/brief",
            params=params,
        )
        works = [{
            "external_id": f"brief:{country}:{line}",
            "title": f"CLI Market intel brief ({country}/{line})",
            "brief": payload,
            "source": "cli_market_intel",
        }]
        return CLIMarketResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )

    def search(
        self,
        *,
        query: str,
        from_publication_date: str,
        limit: int,
        target_market: str | None = None,
        line: str = DEFAULT_LINE,
    ) -> CLIMarketResponse:
        country = (target_market or "US").upper()
        compare = self.compare_products(query=query, country=country, line=line, limit=limit)
        works = list(compare.works)
        try:
            brief = self.intel_brief(country=country, line=line)
            works.extend(brief.works)
        except CLIMarketRequestError:
            pass
        if not works:
            search = self.search_products(query=query, country=country, line=line, limit=limit)
            works.extend(search.works)
        combined = {
            "compare": json.loads(compare.raw_content),
            "works_count": len(works),
        }
        return CLIMarketResponse(
            request_url=compare.request_url,
            request_params={**compare.request_params, "target_market": country, "line": line},
            http_status=compare.http_status,
            raw_content=json.dumps(combined, sort_keys=True).encode("utf-8"),
            works=works,
        )

    def _normalize_compare(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        works: list[dict[str, Any]] = []
        for index, item in enumerate(payload.get("comparison", []) or []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            best_price = item.get("best_price")
            works.append({
                "external_id": f"compare:{index}:{name.casefold()[:80]}",
                "title": name,
                "brand": item.get("brand"),
                "best_price": best_price,
                "best_store": item.get("best_store"),
                "prices": item.get("prices", {}),
                "country": payload.get("country"),
                "source": "cli_market_compare",
            })
        return works

    def _normalize_search(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        works: list[dict[str, Any]] = []
        for item in payload.get("results", []) or []:
            if not isinstance(item, dict):
                continue
            product_id = str(item.get("product_id") or item.get("id") or "").strip()
            name = str(item.get("name") or item.get("title") or "").strip()
            if not product_id and not name:
                continue
            works.append({
                "external_id": product_id or name.casefold(),
                "title": name or product_id,
                "price": item.get("price"),
                "store": item.get("store") or item.get("store_key"),
                "line": item.get("line"),
                "country": payload.get("country"),
                "source": "cli_market_search",
            })
        return works
