"""CORDIS connector for EU funded projects."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class CORDISRequestError(RuntimeError):
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
class CORDISResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class CORDISConnector:
    source = "cordis"
    license_name = "CORDIS Open Data; attribution required"
    base_url = "https://cordis.europa.eu/api/search"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> CORDISResponse:
        params: dict[str, str] = {
            "query": query,
            "startDate": from_publication_date,
            "endDate": "3000-01-01",
            "pageSize": str(limit),
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
            raise CORDISRequestError(
                f"CORDIS returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error
        except URLError as error:
            raise CORDISRequestError(
                f"CORDIS network error: {error.reason}",
                request_url=request_url,
                request_params=params,
            ) from error

        try:
            body = json.loads(raw_content)
            projects = body.get("projects", {}).get("project", [])
            if isinstance(projects, dict):
                projects = [projects]
        except (json.JSONDecodeError, AttributeError, TypeError) as error:
            raise CORDISRequestError(
                "CORDIS response did not contain projects",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error

        works: list[dict[str, Any]] = []
        for project in projects:
            title = project.get("title")
            if not title:
                continue
            works.append({
                "project_id": project.get("id"),
                "title": title,
                "start_date": project.get("startDate"),
                "end_date": project.get("endDate"),
                "funding_amount": project.get("fundingAmount"),
                "currency": project.get("currency"),
                "organizations": project.get("organizations", {}).get("organization", []),
                "source": "cordis",
            })

        return CORDISResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )
