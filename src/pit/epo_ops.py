"""EPO OPS connector for patent intelligence."""

from __future__ import annotations

import base64
import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class EPOOPSRequestError(RuntimeError):
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
class EPOOPSResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class EPOOPSConnector:
    source = "epo_ops"
    license_name = "EPO OPS; free tier with registration"
    # Confirmed live: bare /3.2/rest-services/search 404s -- the real
    # published-data search endpoint has a /published-data/ path segment.
    base_url = "https://ops.epo.org/3.2/rest-services/published-data/search"
    # oauth.epo.org has no DNS record anymore (confirmed live: NXDOMAIN even
    # via 8.8.8.8) -- EPO's Apigee gateway serves the token endpoint from
    # the same host as the API itself, not a separate oauth subdomain.
    token_url = "https://ops.epo.org/3.2/auth/accesstoken"
    # EPO tokens are typically valid ~20min (1200s); used only if the OAuth
    # response omits expires_in. The safety margin refreshes a bit early so a
    # request never starts with a token that expires mid-flight.
    default_token_ttl_seconds = 1140
    token_expiry_safety_margin_seconds = 60

    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        *,
        time_func: Callable[[], float] = time.monotonic,
    ) -> None:
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self._access_token: str | None = None
        self._token_expires_at: float | None = None
        self._time = time_func

    def _get_access_token(self, *, force_refresh: bool = False) -> str:
        if (
            not force_refresh
            and self._access_token
            and self._token_expires_at is not None
            and self._time() < self._token_expires_at
        ):
            return self._access_token
        return self._fetch_new_access_token()

    def _fetch_new_access_token(self) -> str:
        credentials = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode()
        request = Request(
            self.token_url,
            data=b"grant_type=client_credentials",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw_content = response.read()
                http_status = response.status
        except HTTPError as error:
            raw_content = error.read()
            raise EPOOPSRequestError(
                f"EPO OAuth returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=self.token_url,
                request_params={"grant_type": "client_credentials"},
            ) from error
        except URLError as error:
            raise EPOOPSRequestError(
                f"EPO OAuth network error: {error.reason}",
                request_url=self.token_url,
                request_params={"grant_type": "client_credentials"},
            ) from error

        try:
            body = json.loads(raw_content)
            token = body["access_token"]
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise EPOOPSRequestError(
                "EPO OAuth response did not contain access_token",
                http_status=http_status,
                raw_content=raw_content,
                request_url=self.token_url,
                request_params={"grant_type": "client_credentials"},
            ) from error
        try:
            ttl_seconds = int(body.get("expires_in", self.default_token_ttl_seconds))
        except (TypeError, ValueError):
            ttl_seconds = self.default_token_ttl_seconds
        ttl_seconds = max(1, ttl_seconds - self.token_expiry_safety_margin_seconds)
        self._access_token = token
        self._token_expires_at = self._time() + ttl_seconds
        return token

    def search(
        self,
        *,
        query: str,
        from_publication_date: str,
        limit: int,
    ) -> EPOOPSResponse:
        # Confirmed live: range/rows/format are not real query params for
        # this endpoint (400 CLIENT.InvalidQuery) -- date filtering is CQL
        # embedded in `q` itself, and pagination is the X-OPS-Range header,
        # not a query param.
        # Confirmed live: quoting the search term (txt="blueberry") causes a
        # genuine EPO-side 500 (SERVER.DomainAccess), reproduced with plain
        # curl -- unquoted terms work. An open-ended upper bound like
        # "30001231" also 500s -- EPO's date parser rejects far-future
        # years; cap it a few years out instead.
        from_compact = from_publication_date.replace("-", "")
        to_compact = f"{date.today().year + 5}1231"
        cql_query = f'txt={query} and pd within "{from_compact}-{to_compact}"'
        params: dict[str, str] = {"q": cql_query}
        request_url = f"{self.base_url}?{urlencode(params)}"

        # A cached token can be stale even before our own TTL elapses (e.g.
        # EPO revokes/expires it early), so a single 401 triggers one forced
        # refresh + retry before giving up.
        for attempt in (0, 1):
            access_token = self._get_access_token(force_refresh=attempt == 1)
            request = Request(
                request_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                    "X-OPS-Range": f"1-{limit}",
                },
            )
            try:
                with urlopen(request, timeout=20) as response:
                    raw_content = response.read()
                    http_status = response.status
                break
            except HTTPError as error:
                if error.code == 401 and attempt == 0:
                    continue
                raw_content = error.read()
                # EPO reports a genuinely empty result set as HTTP 404 with
                # code SERVER.EntityNotFound -- confirmed live for a
                # non-English query with no matching patents. That's a
                # real, valid "zero patents found" answer, not a request
                # failure; every other domain in this pipeline returns an
                # empty works list for no matches instead of raising.
                if error.code == 404 and b"EntityNotFound" in raw_content:
                    return EPOOPSResponse(
                        request_url=request_url,
                        request_params=params,
                        http_status=200,
                        raw_content=raw_content,
                        works=[],
                    )
                raise EPOOPSRequestError(
                    f"EPO OPS returned HTTP {error.code}",
                    http_status=error.code,
                    raw_content=raw_content,
                    request_url=request_url,
                    request_params=params,
                ) from error
            except URLError as error:
                raise EPOOPSRequestError(
                    f"EPO OPS network error: {error.reason}",
                    request_url=request_url,
                    request_params=params,
                ) from error

        try:
            body = json.loads(raw_content)
            # Confirmed live: the real response nests results under
            # ops:world-patent-data.ops:biblio-search.ops:search-result.
            # ops:publication-reference -- ops:searchResult/ops:result (camelCase)
            # never existed on the real API.
            search_result = (
                body.get("ops:world-patent-data", {})
                .get("ops:biblio-search", {})
                .get("ops:search-result", {})
            )
            results = search_result.get("ops:publication-reference", [])
            if isinstance(results, dict):
                results = [results]
        except (json.JSONDecodeError, AttributeError, TypeError) as error:
            raise EPOOPSRequestError(
                "EPO OPS response did not contain search results",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=params,
            ) from error

        works: list[dict[str, Any]] = []
        for item in results:
            patent = _normalize_patent(item)
            if patent:
                works.append(patent)

        return EPOOPSResponse(
            request_url=request_url,
            request_params=params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )


def _normalize_patent(item: dict[str, Any]) -> dict[str, Any] | None:
    # This is a lightweight publication-reference hit from the /search
    # endpoint -- confirmed live it carries no title/applicant/IPC data at
    # all (that requires a separate per-patent /biblio detail call, out of
    # scope here). Surface what's actually available (family id + the
    # document-id triplet) instead of silently dropping every result via a
    # title check that can never pass against this endpoint's real shape.
    document_id = item.get("document-id", {})
    country = document_id.get("country", {}).get("$", "")
    doc_number = document_id.get("doc-number", {}).get("$", "")
    kind = document_id.get("kind", {}).get("$", "")
    if not doc_number:
        return None
    patent_number = f"{country}{doc_number}{kind}"
    return {
        "patent_number": patent_number,
        "title": "",
        "assignees": [],
        "ipc_codes": [],
        "publication_date": "",
        "family_id": item.get("@family-id", ""),
        "source": "epo_ops",
    }
