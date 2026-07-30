"""Climatiq / Agribalyse connector for carbon footprint."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ClimatiqRequestError(RuntimeError):
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
class ClimatiqResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class ClimatiqConnector:
    source = "climatiq"
    license_name = "Climatiq; commercial with attribution"
    # Confirmed live: /v2/search doesn't exist (404, key was never the
    # problem -- it was already valid). The real search endpoint is
    # /data/v1/search and requires a data_version param.
    base_url = "https://api.climatiq.io/data/v1/search"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def search(self, *, query: str, from_publication_date: str, limit: int) -> ClimatiqResponse:
        params: dict[str, str] = {
            "query": query,
            "results_per_page": str(limit),
            "data_version": "^6",
        }
        request_url = f"{self.base_url}?{urlencode(params)}"
        headers = {"User-Agent": "PIT/0.1 research-service"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(
            request_url,
            headers=headers,
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw_content = response.read()
                http_status = response.status
        except HTTPError as error:
            raw_content = error.read()
            raise ClimatiqRequestError(
                f"Climatiq returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error
        except URLError as error:
            raise ClimatiqRequestError(
                f"Climatiq network error: {error.reason}",
                request_url=request_url,
                request_params=params,
            ) from error

        try:
            body = json.loads(raw_content)
            # Real response is paginated under `results`, not `data`.
            results = body.get("results", [])
        except (json.JSONDecodeError, AttributeError, TypeError) as error:
            raise ClimatiqRequestError(
                "Climatiq response did not contain data",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error

        works: list[dict[str, Any]] = []
        for item in results:
            works.append({
                "activity_id": item.get("activity_id") or item.get("id"),
                "name": item.get("name"),
                "category": item.get("category"),
                "unit": item.get("unit"),
                # Real field name is `factor`, not `co2e_factor`.
                "co2e_factor": item.get("factor"),
                "source": "climatiq",
            })

        return ClimatiqResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )
