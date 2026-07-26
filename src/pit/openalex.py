"""OpenAlex connector for scientific evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class OpenAlexRequestError(RuntimeError):
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
class OpenAlexResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class OpenAlexConnector:
    source = "openalex"
    license_name = "OpenAlex data snapshot; attribution required"
    base_url = "https://api.openalex.org/works"

    def search(
        self,
        *,
        query: str,
        from_publication_date: str,
        limit: int,
    ) -> OpenAlexResponse:
        params: dict[str, str] = {
            "search": query,
            "filter": f"from_publication_date:{from_publication_date}",
            "per-page": str(limit),
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
            raise OpenAlexRequestError(
                f"OpenAlex returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error
        except URLError as error:
            raise OpenAlexRequestError(
                f"OpenAlex network error: {error.reason}",
                request_url=request_url,
                request_params=params,
            ) from error

        try:
            body = json.loads(raw_content)
        except json.JSONDecodeError as error:
            raise OpenAlexRequestError(
                "OpenAlex returned invalid JSON",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error

        works = body.get("results")
        if not isinstance(works, list):
            raise OpenAlexRequestError(
                "OpenAlex response did not contain a results list",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            )
        return OpenAlexResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )
