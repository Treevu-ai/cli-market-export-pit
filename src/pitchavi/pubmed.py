"""PubMed connector using NCBI E-utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class PubMedRequestError(RuntimeError):
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
class PubMedResponse:
    request_url: str
    request_params: dict[str, Any]
    http_status: int
    raw_content: bytes
    works: list[dict[str, Any]]


class PubMedConnector:
    source = "pubmed"
    license_name = "NCBI E-utilities; public domain"
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> PubMedResponse:
        search_params: dict[str, str] = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": str(limit),
            "datetype": "pdat",
            "mindate": from_publication_date,
            "maxdate": "3000",
            "sort": "relevance",
        }
        request_url = f"{self.base_url}?{urlencode(search_params)}"
        request = Request(request_url, headers={"User-Agent": "Pitchavi/0.1 research-service"})
        try:
            with urlopen(request, timeout=20) as response:
                raw_content = response.read()
                http_status = response.status
        except HTTPError as error:
            raw_content = error.read()
            raise PubMedRequestError(
                f"PubMed returned HTTP {error.code}",
                http_status=error.code,
                raw_content=raw_content,
                request_url=request_url,
                request_params=search_params,
            ) from error
        except URLError as error:
            raise PubMedRequestError(
                f"PubMed network error: {error.reason}",
                request_url=request_url,
                request_params=search_params,
            ) from error

        try:
            body = json.loads(raw_content)
            id_list = body["esearchresult"]["idlist"]
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise PubMedRequestError(
                "PubMed response did not contain esearchresult.idlist",
                http_status=http_status,
                raw_content=raw_content,
                request_url=request_url,
                request_params=search_params,
            ) from error

        if not id_list:
            return PubMedResponse(
                request_url=request_url,
                request_params=search_params,
                http_status=http_status,
                raw_content=raw_content,
                works=[],
            )

        summary_params: dict[str, str] = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "json",
            "retmax": str(limit),
        }
        summary_request_url = f"{self.summary_url}?{urlencode(summary_params)}"
        summary_request = Request(summary_request_url, headers={"User-Agent": "Pitchavi/0.1 research-service"})
        try:
            with urlopen(summary_request, timeout=20) as response:
                summary_raw = response.read()
                summary_status = response.status
        except HTTPError as error:
            summary_raw = error.read()
            raise PubMedRequestError(
                f"PubMed summary returned HTTP {error.code}",
                http_status=error.code,
                raw_content=summary_raw,
                request_url=summary_request_url,
                request_params=summary_params,
            ) from error
        except URLError as error:
            raise PubMedRequestError(
                f"PubMed summary network error: {error.reason}",
                request_url=summary_request_url,
                request_params=summary_params,
            ) from error

        try:
            summary_body = json.loads(summary_raw)
            result_items = summary_body["result"]
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise PubMedRequestError(
                "PubMed summary response did not contain result",
                http_status=summary_status,
                raw_content=summary_raw,
                request_url=summary_request_url,
                request_params=summary_params,
            ) from error

        works: list[dict[str, Any]] = []
        for pmid in id_list:
            item = result_items.get(pmid)
            if not item or pmid == "uids":
                continue
            title = item.get("title", "")
            if not title:
                continue
            pub_date = _pubmed_date(item)
            doi = _pubmed_doi(item)
            works.append({
                "pmid": pmid,
                "title": title,
                "publication_date": pub_date,
                "doi": doi,
                "source": "pubmed",
            })

        return PubMedResponse(
            request_url=request_url,
            request_params=search_params,
            http_status=http_status,
            raw_content=raw_content,
            works=works,
        )


def _pubmed_date(item: dict[str, Any]) -> str | None:
    for key in ("pubdate", "epubdate"):
        value = item.get(key)
        if not value:
            continue
        parts = value.split(" ")
        if len(parts) >= 3:
            return f"{parts[0]}-{parts[1]}-{parts[2]}"
    return None


def _pubmed_doi(item: dict[str, Any]) -> str | None:
    for id_obj in item.get("articleids", []):
        if id_obj.get("idtype") == "doi":
            return id_obj.get("value")
    return None
