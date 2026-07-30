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
    # NSF's award search API takes the response-format suffix on the path
    # itself, not a `format` query param -- the previous `/awards/search`
    # + `format=json` shape doesn't match any real NSF route (HTTP 404).
    base_url = "https://api.nsf.gov/services/v1/awards.json"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> NSFAwardsResponse:
        # Confirmed live: NSF's API rejects `startDate`/`endDate`/`limit` as
        # unknown params (AwardAPI-002) -- the real names are `dateStart`/
        # `dateEnd` (MM/DD/YYYY) and `rpp` (results per page, capped at 25).
        year, month, day = from_publication_date.split("-")
        params: dict[str, str] = {
            "keyword": query,
            "dateStart": f"{month}/{day}/{year}",
            "dateEnd": "12/31/2099",
            "rpp": str(min(limit, 25)),
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
            # Confirmed live: the real response nests awards under
            # response.award, not a top-level `award` key.
            awards = body.get("response", {}).get("award", [])
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
                # fundsObligatedAmt is the confirmed-live field name;
                # "amount" doesn't exist on the real response.
                "funding_amount": award.get("fundsObligatedAmt"),
                "currency": "USD",
                "organizations": [n for n in (award.get("awardeeName"), award.get("pdPIName")) if n],
                "source": "nsf_awards",
            })

        return NSFAwardsResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )
