"""Crossref connector for bibliographic metadata enrichment."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class CrossrefRequestError(RuntimeError):
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
class CrossrefResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class CrossrefConnector:
    source = "crossref"
    license_name = "Crossref REST API metadata; attribution and etiquette required"
    base_url = "https://api.crossref.org/works"

    def __init__(self, contact_email: str | None = None) -> None:
        self.contact_email = contact_email

    def search(self, *, query: str, limit: int) -> CrossrefResponse:
        params: dict[str, str] = {
            "query.bibliographic": query,
            "rows": str(limit),
        }
        if self.contact_email:
            params["mailto"] = self.contact_email
        request_url = f"{self.base_url}?{urlencode(params)}"
        headers = {"User-Agent": "PIT/0.1 research-service"}
        if self.contact_email:
            headers["User-Agent"] = f"PIT/0.1 (mailto:{self.contact_email})"
        request = Request(request_url, headers=headers)
        try:
            with urlopen(request, timeout=20) as response:
                raw_content = response.read()
                http_status = response.status
        except HTTPError as error:
            raw_content = error.read()
            raise CrossrefRequestError(
                f"Crossref returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error
        except URLError as error:
            raise CrossrefRequestError(
                f"Crossref network error: {error.reason}",
                request_url=request_url,
                request_params=params,
            ) from error

        try:
            body = json.loads(raw_content)
            works = body["message"]["items"]
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise CrossrefRequestError(
                "Crossref response did not contain message.items",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error
        if not isinstance(works, list):
            raise CrossrefRequestError(
                "Crossref response did not contain a works list",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            )
        return CrossrefResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )
