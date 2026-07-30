"""OpenFDA connector for regulatory discovery."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class OpenFDARequestError(RuntimeError):
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
class OpenFDAResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class OpenFDAConnector:
    source = "openfda"
    license_name = "OpenFDA; public data"
    base_url = "https://api.fda.gov/food/enforcement.json"

    def search(
        self,
        *,
        query: str,
        from_publication_date: str,
        limit: int,
        target_market: str | None = None,
    ) -> OpenFDAResponse:
        if target_market and target_market.upper() != "US":
            return OpenFDAResponse(
                request_url=self.base_url,
                request_params={"search": query, "limit": str(limit), "target_market": target_market or ""},
                http_status=200,
                raw_content=b'{"results":[]}',
                works=[],
            )
        # OpenFDA's Lucene-style syntax requires field-scoped terms (a bare
        # phrase is not a valid query) and report_date literals with no
        # separators (YYYYMMDD) -- both a bare query and hyphenated ISO
        # dates were confirmed live to return HTTP 400.
        date_from = from_publication_date.replace("-", "")
        params: dict[str, str] = {
            "search": f'product_description:"{query}" AND report_date:[{date_from} TO 30001231]',
            "limit": str(limit),
        }
        request_url = f"{self.base_url}?{urlencode(params)}"
        request = Request(
            request_url,
            headers={"User-Agent": "PIT/0.1 research-service"},
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw_content = response.read()
                http_status = response.status
        except HTTPError as error:
            raw_content = error.read()
            raise OpenFDARequestError(
                f"OpenFDA returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error
        except URLError as error:
            raise OpenFDARequestError(
                f"OpenFDA network error: {error.reason}",
                request_url=request_url,
                request_params=params,
            ) from error

        try:
            body = json.loads(raw_content)
            results = body.get("results", [])
        except (json.JSONDecodeError, AttributeError, TypeError) as error:
            raise OpenFDARequestError(
                "OpenFDA response did not contain results",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error

        works: list[dict[str, Any]] = []
        for item in results:
            works.append({
                "recall_number": item.get("recall_number"),
                "status": item.get("status"),
                "classification": item.get("classification"),
                "product_description": item.get("product_description"),
                "reason_for_recall": item.get("reason_for_recall"),
                "source": "openfda",
            })

        return OpenFDAResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )
