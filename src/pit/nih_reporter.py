"""NIH RePORTER connector."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class NIHReporterRequestError(RuntimeError):
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
class NIHReporterResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class NIHReporterConnector:
    source = "nih_reporter"
    license_name = "NIH RePORTER; public data"
    base_url = "https://api.reporter.nih.gov/v2/projects/search"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> NIHReporterResponse:
        params: dict[str, str] = {
            "query": query,
            "from_date": from_publication_date,
            "to_date": "3000-01-01",
            "limit": str(limit),
            "format": "json",
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
            raise NIHReporterRequestError(
                f"NIH RePORTER returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error
        except URLError as error:
            raise NIHReporterRequestError(
                f"NIH RePORTER network error: {error.reason}",
                request_url=request_url,
                request_params=params,
            ) from error

        try:
            body = json.loads(raw_content)
            results = body.get("results", [])
        except (json.JSONDecodeError, AttributeError, TypeError) as error:
            raise NIHReporterRequestError(
                "NIH RePORTER response did not contain results",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error

        works: list[dict[str, Any]] = []
        for item in results:
            title = item.get("project_title")
            if not title:
                continue
            works.append({
                "project_id": item.get("project_number"),
                "title": title,
                "start_date": item.get("start_date"),
                "end_date": item.get("end_date"),
                "funding_amount": item.get("total_cost"),
                "currency": "USD",
                "organizations": item.get("organization", []),
                "source": "nih_reporter",
            })

        return NIHReporterResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )
