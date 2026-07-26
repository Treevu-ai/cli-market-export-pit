"""EFSA / EUR-Lex connector for regulatory discovery."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class EFSALexRequestError(RuntimeError):
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
class EFSALexResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


EU_TARGET_MARKETS = frozenset({"AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"})


class EFSALexConnector:
    source = "efsa_eurlex"
    license_name = "EUR-Lex; open data with attribution"
    base_url = "https://eur-lex.europa.eu/search.html"

    def search(
        self,
        *,
        query: str,
        from_publication_date: str,
        limit: int,
        target_market: str | None = None,
    ) -> EFSALexResponse:
        if target_market and target_market.upper() not in EU_TARGET_MARKETS:
            return EFSALexResponse(
                request_url=self.base_url,
                request_params={"search_text": query, "limit": str(limit), "target_market": target_market or ""},
                http_status=200,
                raw_content=b'{"results":[]}',
                works=[],
            )
        params: dict[str, str] = {
            "search_text": query,
            "from_date": from_publication_date,
            "to_date": "3000-01-01",
            "limit": str(limit),
            "format": "json",
        }
        if target_market:
            params["domain"] = "EUR-Lex"
            params["scope"] = target_market.upper()
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
            raise EFSALexRequestError(
                f"EUR-Lex returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error
        except URLError as error:
            raise EFSALexRequestError(
                f"EUR-Lex network error: {error.reason}",
                request_url=request_url,
                request_params=params,
            ) from error

        try:
            body = json.loads(raw_content)
            results = body.get("results", [])
        except (json.JSONDecodeError, AttributeError, TypeError) as error:
            raise EFSALexRequestError(
                "EUR-Lex response did not contain results",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error

        works: list[dict[str, Any]] = []
        for item in results:
            works.append({
                "celex_number": item.get("celex_number"),
                "title": item.get("title"),
                "date": item.get("date"),
                "type": item.get("type"),
                "source": "efsa_eurlex",
            })

        return EFSALexResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )
