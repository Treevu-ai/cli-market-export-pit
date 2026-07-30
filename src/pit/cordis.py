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
    # Confirmed live via the CORDIS website's own network calls (captured with
    # a real browser session): cordis.europa.eu/api/search never existed --
    # it 404s with the site's SPA shell, not a JSON error. The real endpoint
    # is /api/search/results, and it accepts a Lucene-style `q` query
    # combining a `contenttype='project'` filter (confirmed by toggling the
    # site's own "Projects" collection checkbox) with quoted AND-joined
    # search terms (confirmed by typing a multi-word query into the site's
    # own search box).
    base_url = "https://cordis.europa.eu/api/search/results"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> CORDISResponse:
        terms = query.split()
        terms_clause = " AND ".join(f"'{term}'" for term in terms) if terms else "'*'"
        cql_query = f"contenttype='project' AND ({terms_clause})"
        params: dict[str, str] = {
            "q": cql_query,
            "p": "1",
            "num": str(limit),
            "srt": "Relevance:decreasing",
        }
        request_url = f"{self.base_url}?{urlencode(params)}"
        request = Request(
            request_url,
            headers={"User-Agent": "PIT/0.1 research-service", "Accept": "application/json"},
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
            projects = body.get("payload", {}).get("results", [])
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
            project_id = project.get("reference") or project.get("id")
            if not title or not project_id:
                continue
            if not _within_start_date(project.get("startDate"), from_publication_date):
                continue
            # Confirmed live: the search-results endpoint only returns
            # title/dates/acronym/coordinating-country for a project preview
            # -- funding amount, currency, and participant organizations
            # require a separate per-project detail call, out of scope here.
            # Honest empty placeholders instead of fabricating values.
            works.append({
                "project_id": str(project_id),
                "title": title,
                "start_date": project.get("startDate"),
                "end_date": project.get("endDate"),
                "funding_amount": None,
                "currency": None,
                "organizations": [],
                "source": "cordis",
            })

        return CORDISResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )


def _within_start_date(start_date: str | None, from_publication_date: str) -> bool:
    # CORDIS renders startDate as "1 {{month_07}} 2016" (an untranslated
    # i18n placeholder for the month, confirmed live) -- not machine-
    # parseable as a real date. Fall back to comparing just the year against
    # from_publication_date's year rather than dropping every result.
    if not start_date:
        return True
    year_digits = "".join(char for char in start_date[-4:] if char.isdigit())
    if not year_digits:
        return True
    try:
        return int(year_digits) >= int(from_publication_date[:4])
    except ValueError:
        return True
