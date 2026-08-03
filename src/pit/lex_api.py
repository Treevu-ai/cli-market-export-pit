"""LexAPI connector (lex-api.com) — structured EUR-Lex search, replaces the
unauthenticated eur-lex.europa.eu HTML/JSON scrape for regulatory discovery."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LexAPIRequestError(RuntimeError):
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
class LexAPIResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class LexAPIConnector:
    source = "lex_api"
    license_name = "LexAPI (lex-api.com) — EUR-Lex data; commercial wrapper, attribution required"
    base_url = "https://lex-api.com/api/v1"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("LEX_API_TOKEN")

    def search(
        self,
        *,
        query: str,
        from_publication_date: str,
        limit: int,
        target_market: str | None = None,
    ) -> LexAPIResponse:
        if not self.api_key:
            raise RuntimeError("LexAPI connector is not configured")
        request_url = f"{self.base_url}/search"
        params: dict[str, Any] = {
            "query": query,
            "dateFrom": from_publication_date,
            "domain": "EU_LAW",
            "maxPages": 1,
        }
        request = Request(
            request_url,
            data=json.dumps(params).encode("utf-8"),
            method="POST",
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "User-Agent": "PIT/0.1 research-service",
            },
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw_content = response.read()
                http_status = response.status
        except HTTPError as error:
            raw_content = error.read()
            # 402 = credit pool exhausted, 429 = rate limited — surface these
            # distinctly since they're actionable (top up / back off), unlike
            # a generic HTTP error.
            detail = {
                401: "invalid or missing LEX_API_TOKEN",
                402: "LexAPI credit pool exhausted for this month",
                403: "LexAPI subscription/tier restriction",
                429: "LexAPI rate limit exceeded",
            }.get(error.code, "request failed")
            raise LexAPIRequestError(
                f"LexAPI returned HTTP {error.code} ({detail})",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error
        except (URLError, TimeoutError) as error:
            raise LexAPIRequestError(
                f"LexAPI network error: {error}",
                request_url=request_url,
                request_params=params,
            ) from error

        try:
            body = json.loads(raw_content)
            results = body.get("results", [])
        except (json.JSONDecodeError, AttributeError, TypeError) as error:
            raise LexAPIRequestError(
                "LexAPI response did not contain results",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error

        works: list[dict[str, Any]] = []
        for item in results[:limit]:
            works.append({
                "celex_number": item.get("celexNumber"),
                "title": item.get("title"),
                "date": item.get("dateOfDocument"),
                "type": item.get("documentType"),
                "url": item.get("url"),
                "source": "lex_api",
            })

        return LexAPIResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )
