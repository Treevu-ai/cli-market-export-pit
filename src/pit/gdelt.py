"""GDELT connector for trend/news signals."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class GDELTRequestError(RuntimeError):
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
class GDELTResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class GDELTConnector:
    source = "gdelt"
    license_name = "GDELT Project; open for non-commercial use"
    base_url = "https://api.gdeltproject.org/api/v2/doc/doc"

    def search(
        self,
        *,
        query: str,
        from_publication_date: str,
        limit: int,
        target_market: str | None = None,
    ) -> GDELTResponse:
        scoped_query = query
        if target_market:
            scoped_query = f"{query} sourcecountry:{target_market}"
        params: dict[str, str] = {
            "query": scoped_query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": str(limit),
            "start": from_publication_date.replace("-", ""),
            "end": "30000101",
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
            raise GDELTRequestError(
                f"GDELT returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error
        except URLError as error:
            raise GDELTRequestError(
                f"GDELT network error: {error.reason}",
                request_url=request_url,
                request_params=params,
            ) from error

        try:
            body = json.loads(raw_content)
            articles = body.get("articles", [])
        except (json.JSONDecodeError, AttributeError, TypeError) as error:
            raise GDELTRequestError(
                "GDELT response did not contain articles",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error

        works: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        for article in articles:
            url = article.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            title = article.get("title", "")
            if not title:
                continue
            pub_date = article.get("date")
            if pub_date:
                pub_date = str(pub_date)[:10]
            works.append({
                "url": url,
                "title": title,
                "publication_date": pub_date,
                "source": "gdelt",
                "language": article.get("language"),
                "domain": article.get("domain"),
            })

        return GDELTResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )
