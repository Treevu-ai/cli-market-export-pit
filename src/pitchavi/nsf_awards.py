"""NSF Awards connector."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class NSFAwardsRequestError(RuntimeError):
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
class NSFAwardsResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class NSFAwardsConnector:
    source = "nsf_awards"
    license_name = "NSF Open Data; public domain"
    base_url = "https://api.nsf.gov/services/v1/awards/search"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> NSFAwardsResponse:
        params: dict[str, str] = {
            "keyword": query,
            "startDate": from_publication_date,
            "endDate": "3000-01-01",
            "limit": str(limit),
            "format": "json",
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
            raise NSFAwardsRequestError(
                f"NSF Awards returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error
        except URLError as error:
            raise NSFAwardsRequestError(
                f"NSF Awards network error: {error.reason}",
                request_url=request_url,
                request_params=params,
            ) from error

        try:
            body = json.loads(raw_content)
            awards = body.get("award", [])
        except (json.JSONDecodeError, AttributeError, TypeError) as error:
            raise NSFAwardsRequestError(
                "NSF Awards response did not contain award data",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error

        works: list[dict[str, Any]] = []
        for award in awards:
            title = award.get("title")
            if not title:
                continue
            works.append({
                "project_id": award.get("id"),
                "title": title,
                "start_date": award.get("startDate"),
                "end_date": award.get("expDate"),
                "funding_amount": award.get("amount"),
                "currency": "USD",
                "organizations": award.get("investigator", []),
                "source": "nsf_awards",
            })

        return NSFAwardsResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )
