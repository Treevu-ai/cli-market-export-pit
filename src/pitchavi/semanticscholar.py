"""Semantic Scholar connector for paper search."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class SemanticScholarRequestError(RuntimeError):
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
class SemanticScholarResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class SemanticScholarConnector:
    source = "semanticscholar"
    license_name = "Semantic Scholar Open Data; attribution required"
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> SemanticScholarResponse:
        params: dict[str, str] = {
            "query": query,
            "fields": "title,year,authors,publicationDate,externalIds,citationCount",
            "limit": str(limit),
        }
        if from_publication_date:
            params["year"] = f"{from_publication_date[:4]}-3000"
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
            raise SemanticScholarRequestError(
                f"Semantic Scholar returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error
        except URLError as error:
            raise SemanticScholarRequestError(
                f"Semantic Scholar network error: {error.reason}",
                request_url=request_url,
                request_params=params,
            ) from error

        try:
            body = json.loads(raw_content)
            data_items = body.get("data", [])
        except (json.JSONDecodeError, AttributeError, TypeError) as error:
            raise SemanticScholarRequestError(
                "Semantic Scholar response did not contain data",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error

        works: list[dict[str, Any]] = []
        for item in data_items:
            title = item.get("title")
            if not title:
                continue
            pub_date = item.get("publicationDate") or (f"{item.get('year')}-01-01" if item.get("year") else None)
            external_ids = item.get("externalIds") or {}
            doi = external_ids.get("DOI")
            authors = []
            for author in item.get("authors", []) or []:
                name = author.get("name")
                if name:
                    authors.append({"name": name})
            works.append({
                "paper_id": str(item.get("paperId") or ""),
                "title": title,
                "publication_date": pub_date,
                "doi": doi,
                "source": "semanticscholar",
                "authors": authors,
                "citation_count": item.get("citationCount"),
            })

        return SemanticScholarResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )
