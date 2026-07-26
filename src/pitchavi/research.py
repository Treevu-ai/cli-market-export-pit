"""Research-run orchestration for the scientific evidence slice."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlencode

from .crossref import CrossrefConnector, CrossrefRequestError
from .epo_ops import EPOOPSConnector, EPOOPSRequestError
from .gdelt import GDELTConnector, GDELTRequestError
from .comtrade import ComtradeConnector, ComtradeRequestError
from .openalex import OpenAlexRequestError, OpenAlexResponse
from .pubmed import PubMedConnector, PubMedRequestError
from .scoring import ScoringEngine
from .semanticscholar import SemanticScholarConnector, SemanticScholarRequestError
from .storage import ResearchStore
from .cordis import CORDISConnector, CORDISRequestError
from .nih_reporter import NIHReporterConnector, NIHReporterRequestError
from .nsf_awards import NSFAwardsConnector, NSFAwardsRequestError
from .openfda import OpenFDAConnector, OpenFDARequestError
from .efsa_eurlex import EFSALexConnector, EFSALexRequestError
from .fooddata_central import FoodDataCentralConnector, FoodDataCentralRequestError
from .climatiq import ClimatiqConnector, ClimatiqRequestError


class ScienceConnector(Protocol):
    source: str
    license_name: str
    base_url: str

    def search(self, *, query: str, from_publication_date: str, limit: int) -> OpenAlexResponse: ...


@dataclass(frozen=True)
class ResearchExecutionError(RuntimeError):
    run_id: str
    message: str


def normalize_query(query: str) -> str:
    return " ".join(query.casefold().split())


def _dedupe_key(doi: str, fallback: str) -> str:
    normalized_doi = doi.strip().casefold()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if normalized_doi.startswith(prefix):
            normalized_doi = normalized_doi[len(prefix):]
    return normalized_doi or fallback.strip().casefold()


def _crossref_publication_date(work: dict[str, Any]) -> str | None:
    for key in ("published-print", "published-online", "issued"):
        date_parts = work.get(key, {}).get("date-parts")
        if not isinstance(date_parts, list) or not date_parts or not isinstance(date_parts[0], list):
            continue
        values = date_parts[0]
        if not values:
            continue
        year = int(values[0])
        month = int(values[1]) if len(values) > 1 else 1
        day = int(values[2]) if len(values) > 2 else 1
        return f"{year:04d}-{month:02d}-{day:02d}"
    return None


class ResearchService:
    def __init__(
        self,
        store: ResearchStore,
        science_connector: ScienceConnector | None = None,
        crossref_connector: CrossrefConnector | None = None,
        pubmed_connector: PubMedConnector | None = None,
        semanticscholar_connector: SemanticScholarConnector | None = None,
        patent_connector: EPOOPSConnector | None = None,
        trend_connector: GDELTConnector | None = None,
        trade_connector: ComtradeConnector | None = None,
        cordis_connector: CORDISConnector | None = None,
        nih_connector: NIHReporterConnector | None = None,
        nsf_connector: NSFAwardsConnector | None = None,
        openfda_connector: OpenFDAConnector | None = None,
        efsa_connector: EFSALexConnector | None = None,
        fooddata_connector: FoodDataCentralConnector | None = None,
        climatiq_connector: ClimatiqConnector | None = None,
    ) -> None:
        self.store = store
        self.science_connector = science_connector
        self.crossref_connector = crossref_connector
        self.pubmed_connector = pubmed_connector
        self.semanticscholar_connector = semanticscholar_connector
        self.patent_connector = patent_connector
        self.trend_connector = trend_connector
        self.trade_connector = trade_connector
        self.cordis_connector = cordis_connector
        self.nih_connector = nih_connector
        self.nsf_connector = nsf_connector
        self.openfda_connector = openfda_connector
        self.efsa_connector = efsa_connector
        self.fooddata_connector = fooddata_connector
        self.climatiq_connector = climatiq_connector

    def run_science_research(
        self,
        *,
        query: str,
        target_market: str,
        application: str,
        cutoff_at: str,
        from_publication_date: str,
        limit: int,
    ) -> dict[str, Any]:
        if self.science_connector is None:
            raise RuntimeError("Science connector is not configured")
        run = self.store.create_run(
            query_original=query,
            query_normalized=normalize_query(query),
            target_market=target_market,
            application=application,
            cutoff_at=cutoff_at,
        )
        run_id = run["id"]
        request_id: str | None = None

        try:
            request_params = {
                "search": run["query_normalized"],
                "filter": f"from_publication_date:{from_publication_date}",
                "per-page": str(limit),
            }
            request_url = f"{self.science_connector.base_url}?{urlencode(request_params)}"
            cached = self.store.get_completed_request(
                request_url=request_url,
                request_params=request_params,
            )
            if cached:
                raw_content = self.store.get_raw_by_checksum(cached["checksum"])
                if raw_content:
                    body = json.loads(raw_content)
                    works = body.get("results", [])
                    response = OpenAlexResponse(
                        request_url=cached["request_url"],
                        request_params=json.loads(cached["request_params"]),
                        http_status=200,
                        raw_content=raw_content,
                        works=works,
                    )
                else:
                    response = self.science_connector.search(
                        query=run["query_normalized"],
                        from_publication_date=from_publication_date,
                        limit=limit,
                    )
            else:
                response = self.science_connector.search(
                    query=run["query_normalized"],
                    from_publication_date=from_publication_date,
                    limit=limit,
        )


            request_id = self.store.start_source_request(
                research_run_id=run_id,
                source=self.science_connector.source,
                request_url=response.request_url,
                request_params=response.request_params,
                license_name=self.science_connector.license_name,
            )
            self.store.finish_source_request(
                request_id=request_id,
                http_status=response.http_status,
                raw_content=response.raw_content,
            )
            for work in response.works:
                self._store_work(run_id=run_id, request_id=request_id, work=work)
            self._save_openalex_summary(run_id=run_id, works=response.works)
            self.store.complete_run(run_id)
        except OpenAlexRequestError as error:
            if request_id is None:
                request_params = error.request_params or {
                    "search": run["query_normalized"],
                    "filter": f"from_publication_date:{from_publication_date}",
                    "per-page": str(limit),
                }
                request_url = error.request_url or (
                    f"{self.science_connector.base_url}?{urlencode(request_params)}"
                )
                request_id = self.store.start_source_request(
                    research_run_id=run_id,
                    source=self.science_connector.source,
                    request_url=request_url,
                    request_params=request_params,
                    license_name=self.science_connector.license_name,
                )
            self.store.fail_source_request(
                request_id=request_id,
                http_status=error.http_status,
                error=str(error),
                raw_content=error.raw_content,
            )
            self.store.fail_run(run_id, str(error))
            raise ResearchExecutionError(run_id, str(error)) from error

        return self.store.get_run_detail(run_id)

    def enrich_with_crossref(self, *, run_id: str, limit: int) -> dict[str, Any]:
        if self.crossref_connector is None:
            raise RuntimeError("Crossref connector is not configured")
        run = self.store.get_run(run_id)
        request_id: str | None = None
        try:
            response = self.crossref_connector.search(query=run["query_normalized"], limit=limit)
            request_id = self.store.start_source_request(
                research_run_id=run_id,
                source=self.crossref_connector.source,
                request_url=response.request_url,
                request_params=response.request_params,
                license_name=self.crossref_connector.license_name,
            )
            self.store.finish_source_request(
                request_id=request_id,
                http_status=response.http_status,
                raw_content=response.raw_content,
            )
            for work in response.works:
                self._store_crossref_work(run_id=run_id, request_id=request_id, work=work)
        except CrossrefRequestError as error:
            if request_id is None:
                request_params = error.request_params or {
                    "query.bibliographic": run["query_normalized"],
                    "rows": str(limit),
                }
                request_url = error.request_url or (
                    f"{self.crossref_connector.base_url}?{urlencode(request_params)}"
                )
                request_id = self.store.start_source_request(
                    research_run_id=run_id,
                    source=self.crossref_connector.source,
                    request_url=request_url,
                    request_params=request_params,
                    license_name=self.crossref_connector.license_name,
                )
            self.store.fail_source_request(
                request_id=request_id,
                http_status=error.http_status,
                error=str(error),
                raw_content=error.raw_content,
            )
            raise ResearchExecutionError(run_id, str(error)) from error
        return self.store.get_run_detail(run_id)

    def _store_work(self, *, run_id: str, request_id: str, work: dict[str, Any]) -> None:
        openalex_id = str(work.get("id") or "").strip()
        doi = str(work.get("doi") or "").strip()
        title = str(work.get("title") or "").strip()
        if not openalex_id or not title:
            return
        normalized = {
            "openalex_id": openalex_id,
            "doi": doi or None,
            "title": title,
            "publication_date": work.get("publication_date"),
            "cited_by_count": work.get("cited_by_count"),
            "type": work.get("type"),
            "primary_location": work.get("primary_location"),
        }
        self.store.add_evidence(
            research_run_id=run_id,
            source_request_id=request_id,
            source=self.science_connector.source,
            domain="science",
            external_id=openalex_id,
            title=title,
            published_at=work.get("publication_date"),
            geography=None,
            payload=normalized,
            dedupe_key=_dedupe_key(doi, openalex_id),
        )

    def _store_crossref_work(self, *, run_id: str, request_id: str, work: dict[str, Any]) -> None:
        doi = str(work.get("DOI") or "").strip()
        title_values = work.get("title")
        title = str(title_values[0]).strip() if isinstance(title_values, list) and title_values else ""
        if not doi or not title:
            return
        published_at = _crossref_publication_date(work)
        normalized = {
            "doi": doi,
            "title": title,
            "type": work.get("type"),
            "publisher": work.get("publisher"),
            "published_at": published_at,
            "url": work.get("URL"),
            "author": work.get("author", []),
        }
        self.store.add_evidence(
            research_run_id=run_id,
            source_request_id=request_id,
            source=self.crossref_connector.source if self.crossref_connector else "crossref",
            domain="science",
            external_id=doi,
            title=title,
            published_at=published_at,
            geography=None,
            payload=normalized,
            dedupe_key=_dedupe_key(doi, doi),
        )

    def enrich_with_pubmed(self, *, run_id: str, limit: int) -> dict[str, Any]:
        if self.pubmed_connector is None:
            raise RuntimeError("PubMed connector is not configured")
        run = self.store.get_run(run_id)
        request_id: str | None = None
        try:
            response = self.pubmed_connector.search(
                query=run["query_normalized"],
                from_publication_date="2021-01-01",
                limit=limit,
            )
            request_id = self.store.start_source_request(
                research_run_id=run_id,
                source=self.pubmed_connector.source,
                request_url=response.request_url,
                request_params=response.request_params,
                license_name=self.pubmed_connector.license_name,
            )
            self.store.finish_source_request(
                request_id=request_id,
                http_status=response.http_status,
                raw_content=response.raw_content,
            )
            for work in response.works:
                self._store_pubmed_work(run_id=run_id, request_id=request_id, work=work)
        except PubMedRequestError as error:
            if request_id is None:
                request_id = self.store.start_source_request(
                    research_run_id=run_id,
                    source=self.pubmed_connector.source,
                    request_url=error.request_url or self.pubmed_connector.base_url,
                    request_params=error.request_params or {"query": run["query_normalized"]},
                    license_name=self.pubmed_connector.license_name,
                )
            self.store.fail_source_request(
                request_id=request_id,
                http_status=error.http_status,
                error=str(error),
                raw_content=error.raw_content,
            )
            raise ResearchExecutionError(run_id, str(error)) from error
        return self.store.get_run_detail(run_id)

    def enrich_with_semanticscholar(self, *, run_id: str, limit: int) -> dict[str, Any]:
        if self.semanticscholar_connector is None:
            raise RuntimeError("Semantic Scholar connector is not configured")
        run = self.store.get_run(run_id)
        request_id: str | None = None
        try:
            response = self.semanticscholar_connector.search(
                query=run["query_normalized"],
                from_publication_date="2021-01-01",
                limit=limit,
            )
            request_id = self.store.start_source_request(
                research_run_id=run_id,
                source=self.semanticscholar_connector.source,
                request_url=response.request_url,
                request_params=response.request_params,
                license_name=self.semanticscholar_connector.license_name,
            )
            self.store.finish_source_request(
                request_id=request_id,
                http_status=response.http_status,
                raw_content=response.raw_content,
            )
            for work in response.works:
                self._store_semanticscholar_work(run_id=run_id, request_id=request_id, work=work)
        except SemanticScholarRequestError as error:
            if request_id is None:
                request_id = self.store.start_source_request(
                    research_run_id=run_id,
                    source=self.semanticscholar_connector.source,
                    request_url=error.request_url or self.semanticscholar_connector.base_url,
                    request_params=error.request_params or {"query": run["query_normalized"]},
                    license_name=self.semanticscholar_connector.license_name,
                )
            self.store.fail_source_request(
                request_id=request_id,
                http_status=error.http_status,
                error=str(error),
                raw_content=error.raw_content,
            )
            raise ResearchExecutionError(run_id, str(error)) from error
        return self.store.get_run_detail(run_id)

    def enrich_with_patent(self, *, run_id: str, limit: int) -> dict[str, Any]:
        if self.patent_connector is None:
            raise RuntimeError("Patent connector is not configured")
        run = self.store.get_run(run_id)
        request_id: str | None = None
        try:
            response = self.patent_connector.search(
                query=run["query_normalized"],
                from_publication_date="2021-01-01",
                limit=limit,
            )
            request_id = self.store.start_source_request(
                research_run_id=run_id,
                source=self.patent_connector.source,
                request_url=response.request_url,
                request_params=response.request_params,
                license_name=self.patent_connector.license_name,
            )
            self.store.finish_source_request(
                request_id=request_id,
                http_status=response.http_status,
                raw_content=response.raw_content,
            )
            for work in response.works:
                self._store_patent_work(run_id=run_id, request_id=request_id, work=work)
            self._save_patent_summary(run_id=run_id, works=response.works)
        except EPOOPSRequestError as error:
            if request_id is None:
                request_params = error.request_params or {"q": run["query_normalized"], "rows": str(limit)}
                request_url = error.request_url or self.patent_connector.base_url
                request_id = self.store.start_source_request(
                    research_run_id=run_id,
                    source=self.patent_connector.source,
                    request_url=request_url,
                    request_params=request_params,
                    license_name=self.patent_connector.license_name,
                )
            self.store.fail_source_request(
                request_id=request_id,
                http_status=error.http_status,
                error=str(error),
                raw_content=error.raw_content,
            )
            raise ResearchExecutionError(run_id, str(error)) from error
        return self.store.get_run_detail(run_id)

    def _store_patent_work(self, *, run_id: str, request_id: str, work: dict[str, Any]) -> None:
        patent_number = str(work.get("patent_number") or "").strip()
        title = str(work.get("title") or "").strip()
        if not patent_number or not title:
            return
        normalized = {
            "patent_number": patent_number,
            "title": title,
            "assignees": work.get("assignees", []),
            "ipc_codes": work.get("ipc_codes", []),
            "publication_date": work.get("publication_date"),
            "source": "epo_ops",
        }
        self.store.add_evidence(
            research_run_id=run_id,
            source_request_id=request_id,
            source="epo_ops",
            domain="patent",
            external_id=patent_number,
            title=title,
            published_at=work.get("publication_date"),
            geography=None,
            payload=normalized,
            dedupe_key=patent_number.strip().casefold(),
        )

    def _save_patent_summary(self, *, run_id: str, works: list[dict[str, Any]]) -> None:
        assignee_counter: Counter[str] = Counter()
        ipc_counter: Counter[str] = Counter()
        years: Counter[str] = Counter()
        for work in works:
            for assignee in work.get("assignees", []) or []:
                assignee_counter[assignee] += 1
            for ipc in work.get("ipc_codes", []) or []:
                ipc_counter[ipc] += 1
            pub_date = work.get("publication_date")
            if pub_date:
                year = str(pub_date)[:4]
                if year.isdigit():
                    years[year] += 1
        trend = "stable"
        if len(years) >= 2:
            sorted_years = sorted(years.items())
            if len(sorted_years) >= 2:
                first = sorted_years[0][1]
                last = sorted_years[-1][1]
                if last > first * 1.2:
                    trend = "growing"
                elif last < first * 0.8:
                    trend = "declining"
        self.store.save_domain_summary(
            research_run_id=run_id,
            domain="patent",
            summary_type="epo_ops_aggregation",
            payload={
                "patents_count": len(works),
                "top_assignees": [name for name, _ in assignee_counter.most_common(10)],
                "top_ipc": [code for code, _ in ipc_counter.most_common(10)],
                "filing_trend": trend,
            },
        )

    def _store_pubmed_work(self, *, run_id: str, request_id: str, work: dict[str, Any]) -> None:
        pmid = str(work.get("pmid") or "").strip()
        doi = str(work.get("doi") or "").strip()
        title = str(work.get("title") or "").strip()
        if not pmid or not title:
            return
        normalized = {
            "pmid": pmid,
            "doi": doi or None,
            "title": title,
            "publication_date": work.get("publication_date"),
            "source": "pubmed",
        }
        self.store.add_evidence(
            research_run_id=run_id,
            source_request_id=request_id,
            source="pubmed",
            domain="science",
            external_id=pmid,
            title=title,
            published_at=work.get("publication_date"),
            geography=None,
            payload=normalized,
            dedupe_key=_dedupe_key(doi, pmid),
        )

    def _store_semanticscholar_work(self, *, run_id: str, request_id: str, work: dict[str, Any]) -> None:
        paper_id = str(work.get("paper_id") or "").strip()
        doi = str(work.get("doi") or "").strip()
        title = str(work.get("title") or "").strip()
        if not paper_id or not title:
            return
        normalized = {
            "paper_id": paper_id,
            "doi": doi or None,
            "title": title,
            "publication_date": work.get("publication_date"),
            "authors": work.get("authors", []),
            "citation_count": work.get("citation_count"),
            "source": "semanticscholar",
        }
        self.store.add_evidence(
            research_run_id=run_id,
            source_request_id=request_id,
            source="semanticscholar",
            domain="science",
            external_id=paper_id,
            title=title,
            published_at=work.get("publication_date"),
            geography=None,
            payload=normalized,
            dedupe_key=_dedupe_key(doi, paper_id),
        )

    def _save_openalex_summary(self, *, run_id: str, works: list[dict[str, Any]]) -> None:
        topic_counter: Counter[str] = Counter()
        author_counter: Counter[str] = Counter()
        institution_counter: Counter[str] = Counter()
        for work in works:
            for topic in work.get("topics", []) or []:
                name = topic.get("display_name") or topic.get("topic_name")
                if name:
                    topic_counter[name] += 1
            for authorship in work.get("authorships", []) or []:
                author = authorship.get("author") or {}
                name = author.get("display_name")
                if name:
                    author_counter[name] += 1
                for inst in authorship.get("institutions", []) or []:
                    inst_name = inst.get("display_name")
                    if inst_name:
                        institution_counter[inst_name] += 1
        self.store.save_domain_summary(
            research_run_id=run_id,
            domain="science",
            summary_type="openalex_aggregation",
            payload={
                "top_topics": [name for name, _ in topic_counter.most_common(10)],
                "top_authors": [name for name, _ in author_counter.most_common(10)],
                "top_institutions": [name for name, _ in institution_counter.most_common(10)],
            },
        )

    def enrich_with_trend(self, *, run_id: str, limit: int) -> dict[str, Any]:
        if self.trend_connector is None:
            raise RuntimeError("Trend connector is not configured")
        run = self.store.get_run(run_id)
        request_id: str | None = None
        try:
            response = self.trend_connector.search(
                query=run["query_normalized"],
                from_publication_date="2021-01-01",
                limit=limit,
            )
            request_id = self.store.start_source_request(
                research_run_id=run_id,
                source=self.trend_connector.source,
                request_url=response.request_url,
                request_params=response.request_params,
                license_name=self.trend_connector.license_name,
            )
            self.store.finish_source_request(
                request_id=request_id,
                http_status=response.http_status,
                raw_content=response.raw_content,
            )
            for work in response.works:
                self._store_trend_work(run_id=run_id, request_id=request_id, work=work)
            self._save_trend_summary(run_id=run_id, works=response.works)
        except GDELTRequestError as error:
            if request_id is None:
                request_params = error.request_params or {"query": run["query_normalized"]}
                request_url = error.request_url or self.trend_connector.base_url
                request_id = self.store.start_source_request(
                    research_run_id=run_id,
                    source=self.trend_connector.source,
                    request_url=request_url,
                    request_params=request_params,
                    license_name=self.trend_connector.license_name,
                )
            self.store.fail_source_request(
                request_id=request_id,
                http_status=error.http_status,
                error=str(error),
                raw_content=error.raw_content,
            )
            raise ResearchExecutionError(run_id, str(error)) from error
        return self.store.get_run_detail(run_id)

    def enrich_with_trade(self, *, run_id: str, limit: int, hs_code: str | None = None) -> dict[str, Any]:
        if self.trade_connector is None:
            raise RuntimeError("Trade connector is not configured")
        run = self.store.get_run(run_id)
        request_id: str | None = None
        try:
            response = self.trade_connector.search(
                query=run["query_normalized"],
                from_publication_date="2021-01-01",
                limit=limit,
                hs_code=hs_code,
            )
            request_id = self.store.start_source_request(
                research_run_id=run_id,
                source=self.trade_connector.source,
                request_url=response.request_url,
                request_params=response.request_params,
                license_name=self.trade_connector.license_name,
            )
            self.store.finish_source_request(
                request_id=request_id,
                http_status=response.http_status,
                raw_content=response.raw_content,
            )
            for work in response.works:
                self._store_trade_work(run_id=run_id, request_id=request_id, work=work)
            self._save_trade_summary(run_id=run_id, works=response.works)
        except ComtradeRequestError as error:
            if request_id is None:
                request_params = error.request_params or {"query": run["query_normalized"]}
                request_url = error.request_url or self.trade_connector.base_url
                request_id = self.store.start_source_request(
                    research_run_id=run_id,
                    source=self.trade_connector.source,
                    request_url=request_url,
                    request_params=request_params,
                    license_name=self.trade_connector.license_name,
                )
            self.store.fail_source_request(
                request_id=request_id,
                http_status=error.http_status,
                error=str(error),
                raw_content=error.raw_content,
            )
            raise ResearchExecutionError(run_id, str(error)) from error
        return self.store.get_run_detail(run_id)

    def _store_trend_work(self, *, run_id: str, request_id: str, work: dict[str, Any]) -> None:
        url = str(work.get("url") or "").strip()
        title = str(work.get("title") or "").strip()
        if not url or not title:
            return
        normalized = {
            "url": url,
            "title": title,
            "publication_date": work.get("publication_date"),
            "language": work.get("language"),
            "domain": work.get("domain"),
            "source": "gdelt",
        }
        self.store.add_evidence(
            research_run_id=run_id,
            source_request_id=request_id,
            source="gdelt",
            domain="trend",
            external_id=url,
            title=title,
            published_at=work.get("publication_date"),
            geography=None,
            payload=normalized,
            dedupe_key=url.strip().casefold(),
        )

    def _store_trade_work(self, *, run_id: str, request_id: str, work: dict[str, Any]) -> None:
        reporter = str(work.get("reporter") or "").strip()
        partner = str(work.get("partner") or "").strip()
        period = str(work.get("period") or "").strip()
        if not reporter or not partner or not period:
            return
        external_id = f"{reporter}-{partner}-{period}-{work.get('hs_code', '')}"
        normalized = {
            "reporter": reporter,
            "partner": partner,
            "flow": work.get("flow"),
            "period": period,
            "trade_value_usd": work.get("trade_value_usd"),
            "net_weight_kg": work.get("net_weight_kg"),
            "hs_code": work.get("hs_code"),
            "source": "comtrade",
        }
        self.store.add_evidence(
            research_run_id=run_id,
            source_request_id=request_id,
            source="comtrade",
            domain="trade",
            external_id=external_id,
            title=f"Trade flow: {reporter} -> {partner} ({period})",
            published_at=f"{period}-01-01" if len(period) == 4 else period,
            geography=partner,
            payload=normalized,
            dedupe_key=external_id.strip().casefold(),
        )

    def _save_trend_summary(self, *, run_id: str, works: list[dict[str, Any]]) -> None:
        domain_counter: Counter[str] = Counter()
        language_counter: Counter[str] = Counter()
        years: Counter[str] = Counter()
        for work in works:
            domain = work.get("domain")
            if domain:
                domain_counter[domain] += 1
            language = work.get("language")
            if language:
                language_counter[language] += 1
            pub_date = work.get("publication_date")
            if pub_date:
                year = str(pub_date)[:4]
                if year.isdigit():
                    years[year] += 1
        trend = "stable"
        if len(years) >= 2:
            sorted_years = sorted(years.items())
            if len(sorted_years) >= 2:
                first = sorted_years[0][1]
                last = sorted_years[-1][1]
                if last > first * 1.2:
                    trend = "growing"
                elif last < first * 0.8:
                    trend = "declining"
        self.store.save_domain_summary(
            research_run_id=run_id,
            domain="trend",
            summary_type="gdelt_aggregation",
            payload={
                "news_volume": len(works),
                "trend": trend,
                "top_domains": [name for name, _ in domain_counter.most_common(10)],
                "top_languages": [name for name, _ in language_counter.most_common(10)],
            },
        )

    def _save_trade_summary(self, *, run_id: str, works: list[dict[str, Any]]) -> None:
        reporter_counter: Counter[str] = Counter()
        partner_counter: Counter[str] = Counter()
        flow_counter: Counter[str] = Counter()
        years: Counter[str] = Counter()
        for work in works:
            reporter = work.get("reporter")
            partner = work.get("partner")
            flow = work.get("flow")
            if reporter:
                reporter_counter[reporter] += 1
            if partner:
                partner_counter[partner] += 1
            if flow:
                flow_counter[flow] += 1
            period = work.get("period")
            if period:
                year = str(period)[:4]
                if year.isdigit():
                    years[year] += 1
        trend = "stable"
        if len(years) >= 2:
            sorted_years = sorted(years.items())
            if len(sorted_years) >= 2:
                first = sorted_years[0][1]
                last = sorted_years[-1][1]
                if last > first * 1.2:
                    trend = "growing"
                elif last < first * 0.8:
                    trend = "declining"
        self.store.save_domain_summary(
            research_run_id=run_id,
            domain="trade",
            summary_type="comtrade_aggregation",
            payload={
                "trade_records_count": len(works),
                "trend": trend,
                "top_reporters": [name for name, _ in reporter_counter.most_common(10)],
                "top_partners": [name for name, _ in partner_counter.most_common(10)],
                "flows": [name for name, _ in flow_counter.most_common(10)],
            },
        )

    def _estimate_coverage(self, domain: str, summary: dict[str, Any]) -> float:
        if not summary:
            return 0.0
        if domain == "science":
            return 0.9 if summary.get("openalex_aggregation") else 0.4
        if domain == "patent":
            return 0.9 if summary.get("epo_ops_aggregation") else 0.0
        if domain == "trend":
            return 0.8 if summary.get("gdelt_aggregation") else 0.0
        if domain == "trade":
            return 0.9 if summary.get("comtrade_aggregation") else 0.0
        return 0.0

    def _estimate_score(self, domain: str, summary: dict[str, Any]) -> int:
        if not summary:
            return 0
        if domain == "science":
            agg = summary.get("openalex_aggregation", {})
            count = len(agg.get("top_topics", []))
            return min(100, max(0, count * 10))
        if domain == "patent":
            agg = summary.get("epo_ops_aggregation", {})
            count = agg.get("patents_count", 0)
            return min(100, max(0, count * 5))
        if domain == "trend":
            agg = summary.get("gdelt_aggregation", {})
            count = agg.get("news_volume", 0)
            return min(100, max(0, count * 5))
        if domain == "trade":
            agg = summary.get("comtrade_aggregation", {})
            count = agg.get("trade_records_count", 0)
            return min(100, max(0, count * 20))
        return 0

    def _build_claims(self, run_id: str, domain_scores: list[dict[str, Any]], result: dict[str, Any]) -> list[dict[str, Any]]:
        claims = []
        for item in domain_scores:
            domain = item["domain"]
            score = item["score"]
            claims.append({
                "domain": domain,
                "statement": f"{domain.capitalize()} score estimated from available evidence.",
                "value": score,
                "unit": "index",
                "method": "heuristic_v1",
                "period_from": None,
                "period_to": None,
                "geography": None,
                "confidence": item["confidence"],
                "limitations": "Automated estimation; human review recommended.",
                "source_refs": [run_id],
            })
        claims.append({
            "domain": "opportunity",
            "statement": f"Opportunity score calculated with coverage factor {result['coverage_factor']:.2f}.",
            "value": result["opportunity_score"],
            "unit": "index",
            "method": "weighted_sum_v1",
            "period_from": None,
            "period_to": None,
            "geography": None,
            "confidence": "medium",
            "limitations": "Weights are initial hypothesis; calibration pending.",
            "source_refs": [run_id],
        })
        return claims

    def enrich_with_regulatory(self, *, run_id: str, limit: int) -> dict[str, Any]:
        run = self.store.get_run(run_id)
        connectors = [
            ("openfda", self.openfda_connector, OpenFDARequestError),
            ("efsa_eurlex", self.efsa_connector, EFSALexRequestError),
            ("fooddata_central", self.fooddata_connector, FoodDataCentralRequestError),
        ]
        for source, connector, error_cls in connectors:
            if connector is None:
                continue
            request_id: str | None = None
            try:
                response = connector.search(
                    query=run["query_normalized"],
                    from_publication_date="2021-01-01",
                    limit=limit,
                )
                request_id = self.store.start_source_request(
                    research_run_id=run_id,
                    source=connector.source,
                    request_url=response.request_url,
                    request_params=response.request_params,
                    license_name=connector.license_name,
                )
                self.store.finish_source_request(
                    request_id=request_id,
                    http_status=response.http_status,
                    raw_content=response.raw_content,
                )
                for work in response.works:
                    self._store_regulatory_work(run_id=run_id, request_id=request_id, work=work, source=connector.source)
            except (OpenFDARequestError, EFSALexRequestError, FoodDataCentralRequestError) as error:
                if request_id is None:
                    request_params = error.request_params or {"query": run["query_normalized"]}
                    request_url = error.request_url or connector.base_url
                    request_id = self.store.start_source_request(
                        research_run_id=run_id,
                        source=connector.source,
                        request_url=request_url,
                        request_params=request_params,
                        license_name=connector.license_name,
                    )
                self.store.fail_source_request(
                    request_id=request_id,
                    http_status=error.http_status,
                    error=str(error),
                    raw_content=error.raw_content,
                )
        self._save_regulatory_summary(run_id=run_id)
        return self.store.get_run_detail(run_id)

    def _store_regulatory_work(self, *, run_id: str, request_id: str, work: dict[str, Any], source: str) -> None:
        external_id = str(work.get("recall_number") or work.get("celex_number") or work.get("fdc_id") or "").strip()
        title = str(work.get("title") or work.get("product_description") or work.get("reason_for_recall") or "").strip()
        if not external_id or not title:
            return
        normalized = {
            "external_id": external_id,
            "title": title,
            "status": work.get("status"),
            "classification": work.get("classification"),
            "date": work.get("date"),
            "source": source,
        }
        self.store.add_evidence(
            research_run_id=run_id,
            source_request_id=request_id,
            source=source,
            domain="regulatory",
            external_id=external_id,
            title=title,
            published_at=work.get("date"),
            geography=None,
            payload=normalized,
            dedupe_key=f"{source}:{external_id}".strip().casefold(),
        )

    def _save_regulatory_summary(self, *, run_id: str) -> None:
        with self.store._transaction() as db:
            rows = db.execute(
                "SELECT source, COUNT(*) as count FROM evidence_records WHERE research_run_id=? AND domain='regulatory' GROUP BY source",
                (run_id,),
            ).fetchall()
        sources = []
        for row in rows:
            sources.append({
                "source": row["source"],
                "record_count": row["count"],
            })
        self.store.save_domain_summary(
            research_run_id=run_id,
            domain="regulatory",
            summary_type="regulatory_aggregation",
            payload={
                "sources": sources,
                "total_records": sum(s["record_count"] for s in sources),
            },
        )

    def enrich_with_sustainability(self, *, run_id: str, limit: int) -> dict[str, Any]:
        if self.climatiq_connector is None:
            raise RuntimeError("Climatiq connector is not configured")
        run = self.store.get_run(run_id)
        request_id: str | None = None
        try:
            response = self.climatiq_connector.search(
                query=run["query_normalized"],
                from_publication_date="2021-01-01",
                limit=limit,
            )
            request_id = self.store.start_source_request(
                research_run_id=run_id,
                source=self.climatiq_connector.source,
                request_url=response.request_url,
                request_params=response.request_params,
                license_name=self.climatiq_connector.license_name,
            )
            self.store.finish_source_request(
                request_id=request_id,
                http_status=response.http_status,
                raw_content=response.raw_content,
            )
            for work in response.works:
                self._store_sustainability_work(run_id=run_id, request_id=request_id, work=work)
            self._save_sustainability_summary(run_id=run_id, works=response.works)
        except ClimatiqRequestError as error:
            if request_id is None:
                request_params = error.request_params or {"query": run["query_normalized"]}
                request_url = error.request_url or self.climatiq_connector.base_url
                request_id = self.store.start_source_request(
                    research_run_id=run_id,
                    source=self.climatiq_connector.source,
                    request_url=request_url,
                    request_params=request_params,
                    license_name=self.climatiq_connector.license_name,
                )
            self.store.fail_source_request(
                request_id=request_id,
                http_status=error.http_status,
                error=str(error),
                raw_content=error.raw_content,
            )
            raise ResearchExecutionError(run_id, str(error)) from error
        return self.store.get_run_detail(run_id)

    def _store_sustainability_work(self, *, run_id: str, request_id: str, work: dict[str, Any]) -> None:
        activity_id = str(work.get("activity_id") or "").strip()
        name = str(work.get("name") or "").strip()
        if not activity_id or not name:
            return
        normalized = {
            "activity_id": activity_id,
            "name": name,
            "category": work.get("category"),
            "unit": work.get("unit"),
            "co2e_factor": work.get("co2e_factor"),
            "source": "climatiq",
        }
        self.store.add_evidence(
            research_run_id=run_id,
            source_request_id=request_id,
            source="climatiq",
            domain="sustainability",
            external_id=activity_id,
            title=name,
            published_at=None,
            geography=None,
            payload=normalized,
            dedupe_key=f"climatiq:{activity_id}".strip().casefold(),
        )

    def _save_sustainability_summary(self, *, run_id: str, works: list[dict[str, Any]]) -> None:
        category_counter: Counter[str] = Counter()
        unit_counter: Counter[str] = Counter()
        factors = []
        for work in works:
            category = work.get("category")
            unit = work.get("unit")
            if category:
                category_counter[category] += 1
            if unit:
                unit_counter[unit] += 1
            factor = work.get("co2e_factor")
            if factor is not None:
                factors.append(float(factor))
        avg_factor = sum(factors) / len(factors) if factors else None
        self.store.save_domain_summary(
            research_run_id=run_id,
            domain="sustainability",
            summary_type="climatiq_aggregation",
            payload={
                "activity_count": len(works),
                "top_categories": [name for name, _ in category_counter.most_common(10)],
                "units": [name for name, _ in unit_counter.most_common(10)],
                "avg_co2e_factor": avg_factor,
            },
        )


    def enrich_with_techscout(self, *, run_id: str, limit: int) -> dict[str, Any]:
        run = self.store.get_run(run_id)
        connectors = [
            ("cordis", self.cordis_connector, CORDISRequestError),
            ("nih_reporter", self.nih_connector, NIHReporterRequestError),
            ("nsf_awards", self.nsf_connector, NSFAwardsRequestError),
        ]
        for source, connector, error_cls in connectors:
            if connector is None:
                continue
            request_id: str | None = None
            try:
                response = connector.search(
                    query=run["query_normalized"],
                    from_publication_date="2021-01-01",
                    limit=limit,
                )
                request_id = self.store.start_source_request(
                    research_run_id=run_id,
                    source=connector.source,
                    request_url=response.request_url,
                    request_params=response.request_params,
                    license_name=connector.license_name,
                )
                self.store.finish_source_request(
                    request_id=request_id,
                    http_status=response.http_status,
                    raw_content=response.raw_content,
                )
                for work in response.works:
                    self._store_techscout_work(run_id=run_id, request_id=request_id, work=work)
            except (CORDISRequestError, NIHReporterRequestError, NSFAwardsRequestError) as error:
                if request_id is None:
                    request_params = error.request_params or {"query": run["query_normalized"]}
                    request_url = error.request_url or connector.base_url
                    request_id = self.store.start_source_request(
                        research_run_id=run_id,
                        source=connector.source,
                        request_url=request_url,
                        request_params=request_params,
                        license_name=connector.license_name,
                    )
                self.store.fail_source_request(
                    request_id=request_id,
                    http_status=error.http_status,
                    error=str(error),
                    raw_content=error.raw_content,
                )
        self._save_techscout_summary(run_id=run_id)
        return self.store.get_run_detail(run_id)

    def _store_techscout_work(self, *, run_id: str, request_id: str, work: dict[str, Any]) -> None:
        external_id = str(work.get("project_id") or "").strip()
        title = str(work.get("title") or "").strip()
        if not external_id or not title:
            return
        normalized = {
            "external_id": external_id,
            "title": title,
            "start_date": work.get("start_date"),
            "end_date": work.get("end_date"),
            "funding_amount": work.get("funding_amount"),
            "currency": work.get("currency"),
            "organizations": work.get("organizations", []),
            "source": work.get("source"),
        }
        self.store.add_evidence(
            research_run_id=run_id,
            source_request_id=request_id,
            source=work.get("source", "techscout"),
            domain="technology_scout",
            external_id=external_id,
            title=title,
            published_at=work.get("start_date"),
            geography=None,
            payload=normalized,
            dedupe_key=f"{work.get('source', 'techscout')}:{external_id}".strip().casefold(),
        )

    def _save_techscout_summary(self, *, run_id: str) -> None:
        with self.store._transaction() as db:
            rows = db.execute(
                "SELECT source, COUNT(*) as count FROM evidence_records WHERE research_run_id=? AND domain='technology_scout' GROUP BY source",
                (run_id,),
            ).fetchall()
        sources = []
        for row in rows:
            sources.append({
                "source": row["source"],
                "project_count": row["count"],
            })
        self.store.save_domain_summary(
            research_run_id=run_id,
            domain="technology_scout",
            summary_type="techscout_aggregation",
            payload={
                "sources": sources,
                "total_projects": sum(s["project_count"] for s in sources),
            },
        )

class ScoringService:
    def __init__(self, store: ResearchStore) -> None:
        self.store = store

    def calculate_scores(self, run_id: str) -> dict[str, Any]:
        run = self.store.get_run(run_id)
        summaries = self.store.get_domain_summaries(run_id)
        domain_scores = []
        for domain, payloads in summaries.items():
            payload = next(iter(payloads.values()), {}) if payloads else {}
            score = self._estimate_score(domain, payload)
            confidence = "high" if self._estimate_coverage(domain, payload) > 0.7 else "medium"
            domain_scores.append({
                "domain": domain,
                "score": score,
                "confidence": confidence,
            })
        coverage_factor = sum(item["confidence"] == "high" for item in domain_scores) / max(len(domain_scores), 1)
        opportunity_score = int(sum(item["score"] for item in domain_scores) / max(len(domain_scores), 1) * coverage_factor)
        result = {
            "score_version": "v1",
            "coverage_factor": coverage_factor,
            "opportunity_score": opportunity_score,
            "recommendation": "pursue" if opportunity_score >= 60 else "monitor",
            "dimensions": ["science", "patent", "trend", "trade"],
            "alerts": [],
            "exclusions": [],
        }
        claims = self._build_claims(run_id, domain_scores, result)
        for claim in claims:
            self.store.save_claim(
                research_run_id=run_id,
                domain=claim["domain"],
                statement=claim["statement"],
                value=claim["value"],
                unit=claim["unit"],
                method=claim["method"],
                period_from=claim["period_from"],
                period_to=claim["period_to"],
                geography=claim["geography"],
                confidence=claim["confidence"],
                limitations=claim["limitations"],
                source_refs=claim["source_refs"],
            )
        return result

    def _estimate_coverage(self, domain: str, summary: dict[str, Any]) -> float:
        if not summary:
            return 0.0
        if domain == "science":
            return 0.9 if summary.get("openalex_aggregation") else 0.4
        if domain == "patent":
            return 0.9 if summary.get("epo_ops_aggregation") else 0.0
        if domain == "trend":
            return 0.8 if summary.get("gdelt_aggregation") else 0.0
        if domain == "trade":
            return 0.9 if summary.get("comtrade_aggregation") else 0.0
        return 0.0

    def _estimate_score(self, domain: str, summary: dict[str, Any]) -> int:
        if not summary:
            return 0
        if domain == "science":
            agg = summary.get("openalex_aggregation", {})
            count = len(agg.get("top_topics", []))
            return min(100, max(0, count * 10))
        if domain == "patent":
            agg = summary.get("epo_ops_aggregation", {})
            count = agg.get("patents_count", 0)
            return min(100, max(0, count * 5))
        if domain == "trend":
            agg = summary.get("gdelt_aggregation", {})
            count = agg.get("news_volume", 0)
            return min(100, max(0, count * 5))
        if domain == "trade":
            agg = summary.get("comtrade_aggregation", {})
            count = agg.get("trade_records_count", 0)
            return min(100, max(0, count * 20))
        return 0

    def _build_claims(self, run_id: str, domain_scores: list[dict[str, Any]], result: dict[str, Any]) -> list[dict[str, Any]]:
        claims = []
        for item in domain_scores:
            domain = item["domain"]
            score = item["score"]
            claims.append({
                "domain": domain,
                "statement": f"{domain.capitalize()} score estimated from available evidence.",
                "value": score,
                "unit": "index",
                "method": "heuristic_v1",
                "period_from": None,
                "period_to": None,
                "geography": None,
                "confidence": item["confidence"],
                "limitations": "Automated estimation; human review recommended.",
                "source_refs": [run_id],
            })
        claims.append({
            "domain": "opportunity",
            "statement": f"Opportunity score calculated with coverage factor {result['coverage_factor']:.2f}.",
            "value": result["opportunity_score"],
            "unit": "index",
            "method": "weighted_sum_v1",
            "period_from": None,
            "period_to": None,
            "geography": None,
            "confidence": "medium",
            "limitations": "Weights are initial hypothesis; calibration pending.",
            "source_refs": [run_id],
        })
        return claims
