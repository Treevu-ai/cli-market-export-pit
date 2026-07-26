"""EPO OPS connector for patent intelligence."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
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
    base_url = "https://ops.epo.org/3.2/rest-services/search"
    token_url = "https://oauth.epo.org/oauth2/token"

    def __init__(self, consumer_key: str, consumer_secret: str) -> None:
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self._access_token: str | None = None

    def _get_access_token(self) -> str:
        if self._access_token:
            return self._access_token
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
        self._access_token = token
        return token

    def search(
        self,
        *,
        query: str,
        from_publication_date: str,
        limit: int,
    ) -> EPOOPSResponse:
        params: dict[str, str] = {
            "q": query,
            "range": f"{from_publication_date[:4]}-3000",
            "rows": str(limit),
            "format": "json",
        }
        request_url = f"{self.base_url}?{urlencode(params)}"
        access_token = self._get_access_token()
        request = Request(
            request_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw_content = response.read()
                http_status = response.status
        except HTTPError as error:
            raw_content = error.read()
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
            results = body.get("ops:searchResult", {}).get("ops:result", [])
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
    pub_ref = item.get("ops:publicationReference", {})
    app_ref = item.get("ops:applicationReference", {})
    title = item.get("ops:title", "")
    if not title:
        return None
    patent_number = pub_ref.get("dc:identifier", "")
    if not patent_number:
        patent_number = app_ref.get("dc:identifier", "")
    applicants = item.get("ops:applicants", {}).get("ops:applicant", [])
    if isinstance(applicants, dict):
        applicants = [applicants]
    assignees = []
    for applicant in applicants:
        name = applicant.get("ops:name", "")
        if name:
            assignees.append(name)
    classifications = item.get("ops:classifications", {}).get("ops:classification", [])
    if isinstance(classifications, dict):
        classifications = [classifications]
    ipc_codes = []
    for cls in classifications:
        code = cls.get("ops:classificationSymbol", "")
        if code:
            ipc_codes.append(code)
    pub_date = pub_ref.get("ops:date", "")
    if not pub_date:
        pub_date = app_ref.get("ops:date", "")
    return {
        "patent_number": patent_number,
        "title": title,
        "assignees": assignees,
        "ipc_codes": ipc_codes,
        "publication_date": pub_date,
        "source": "epo_ops",
    }
