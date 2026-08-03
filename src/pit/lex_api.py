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

    # EUR-Lex's own search is a literal keyword match, not semantic -- confirmed
    # live: bare fruit names ("mango", "camu camu") and even name+topic
    # combinations ("mango plant health", "mango maximum residue") all return
    # zero results, while broad EU food-law terms alone return thousands.
    # There is no product-specific fallback that reliably matches; the only
    # working fallback is the general regulatory framework a fresh-produce
    # import would fall under, searched WITHOUT the product name mixed in.
    # "Plant health" (the EU's phytosanitary import framework, Reg. (EU)
    # 2016/2031) is the most on-topic single term for agricultural imports.
    _FALLBACK_QUERY = "plant health"

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

        http_status, raw_content, results, request_url, params = self._search_once(
            query_text=query, from_publication_date=from_publication_date
        )
        is_fallback = False
        if not results and query.strip().casefold() != self._FALLBACK_QUERY:
            is_fallback = True
            # No dateFrom here, deliberately: the fallback searches for the
            # standing regulatory framework (e.g. Reg. (EU) 2016/2031 on
            # plant health), which predates most research runs' publication
            # window -- confirmed live, "plant health" + dateFrom=2021-01-01
            # returns 0 results while the same query with no date filter
            # returns 7000+. A framework regulation being in force matters
            # regardless of when it was adopted.
            http_status, raw_content, results, request_url, params = self._search_once(
                query_text=self._FALLBACK_QUERY, from_publication_date=None
            )

        works: list[dict[str, Any]] = []
        for item in results[:limit]:
            title = item.get("title")
            if is_fallback and title:
                title = f"[Marco general — no específico de '{query}'] {title}"
            works.append({
                "celex_number": item.get("celexNumber"),
                "title": title,
                "date": item.get("dateOfDocument"),
                "type": item.get("documentType"),
                "url": item.get("url"),
                "source": "lex_api",
                "is_generic_fallback": is_fallback,
            })

        return LexAPIResponse(
            request_url=request_url,
            request_params={**params, "fallback_applied": is_fallback},
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )

    def _search_once(
        self, *, query_text: str, from_publication_date: str | None
    ) -> tuple[int, bytes, list[dict[str, Any]], str, dict[str, Any]]:
        request_url = f"{self.base_url}/search"
        params: dict[str, Any] = {
            "query": query_text,
            # No "domain" param, deliberately: "domain": "EU_LAW" (a documented
            # valid value) reliably returns 0 results on the live API --
            # confirmed by A/B testing the identical query with and without
            # it ("plant health": 0 with domain=EU_LAW, 7180 with domain=ALL
            # or omitted). Omitting matches the working "ALL"/default behavior
            # without depending on which value LexAPI's domain filter is
            # actually broken for.
            "maxPages": 1,
        }
        if from_publication_date:
            params["dateFrom"] = from_publication_date
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

        return http_status, raw_content, results, request_url, params
