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
from .semanticscholar import SemanticScholarConnector, SemanticScholarRequestError
from .storage import ResearchStore
from .cordis import CORDISConnector, CORDISRequestError
from .nih_reporter import NIHReporterConnector, NIHReporterRequestError
from .nsf_awards import NSFAwardsConnector, NSFAwardsRequestError
from .openfda import OpenFDAConnector, OpenFDARequestError
from .efsa_eurlex import EFSALexConnector, EFSALexRequestError
from .fooddata_central import FoodDataCentralConnector, FoodDataCentralRequestError
from .climatiq import ClimatiqConnector, ClimatiqRequestError
from .climarket import CLIMarketConnector, CLIMarketRequestError
from .taxonomy import ensure_default_taxonomy, expand_query_with_synonyms, resolve_hs_code


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


def _run_context(run: dict[str, Any]) -> tuple[str, str, str]:
    return (
        run["query_normalized"],
        run.get("from_publication_date") or "2021-01-01",
        run.get("target_market") or "US",
    )


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
        if not values or values[0] is None:
            continue
        try:
            year = int(values[0])
            month = int(values[1]) if len(values) > 1 and values[1] is not None else 1
            day = int(values[2]) if len(values) > 2 and values[2] is not None else 1
        except (TypeError, ValueError):
            continue
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
        commerce_connector: CLIMarketConnector | None = None,
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
        self.commerce_connector = commerce_connector

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
        ensure_default_taxonomy(self.store)
        run = self.store.create_run(
            query_original=query,
            query_normalized=normalize_query(query),
            target_market=target_market,
            application=application,
            cutoff_at=cutoff_at,
            from_publication_date=from_publication_date,
        )
        run_id = run["id"]
        search_query = expand_query_with_synonyms(
            self.store,
            taxonomy_version=run["taxonomy_version"],
            query_normalized=run["query_normalized"],
        )
        request_id: str | None = None

        try:
            request_params = {
                "search": search_query,
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
                        query=search_query,
                        from_publication_date=from_publication_date,
                        limit=limit,
                    )
            else:
                response = self.science_connector.search(
                    query=search_query,
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
                self._store_work(run_id=run_id, request_id=request_id, work=work, source=self.science_connector.source)
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

    def _store_work(self, *, run_id: str, request_id: str, work: dict[str, Any], source: str) -> None:
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
            source=source,
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
        query, from_date, _target_market = _run_context(run)
        request_id: str | None = None
        try:
            response = self.pubmed_connector.search(
                query=query,
                from_publication_date=from_date,
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
        query, from_date, _target_market = _run_context(run)
        request_id: str | None = None
        try:
            response = self.semanticscholar_connector.search(
                query=query,
                from_publication_date=from_date,
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
        query, from_date, _target_market = _run_context(run)
        request_id: str | None = None
        try:
            response = self.patent_connector.search(
                query=query,
                from_publication_date=from_date,
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
        query, from_date, target_market = _run_context(run)
        request_id: str | None = None
        try:
            response = self.trend_connector.search(
                query=query,
                from_publication_date=from_date,
                limit=limit,
                target_market=target_market,
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
        query, from_date, target_market = _run_context(run)
        resolved_hs = hs_code or resolve_hs_code(
            self.store,
            taxonomy_version=run["taxonomy_version"],
            query_normalized=query,
        )
        request_id: str | None = None
        try:
            response = self.trade_connector.search(
                query=query,
                from_publication_date=from_date,
                limit=limit,
                hs_code=resolved_hs,
                target_market=target_market,
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

    def enrich_with_commerce(self, *, run_id: str, limit: int, line: str = "supermercados") -> dict[str, Any]:
        if self.commerce_connector is None:
            raise RuntimeError("CLI Market connector is not configured")
        run = self.store.get_run(run_id)
        query, from_date, target_market = _run_context(run)
        request_id: str | None = None
        try:
            response = self.commerce_connector.search(
                query=query,
                from_publication_date=from_date,
                limit=limit,
                target_market=target_market,
                line=line,
            )
            request_id = self.store.start_source_request(
                research_run_id=run_id,
                source=self.commerce_connector.source,
                request_url=response.request_url,
                request_params=response.request_params,
                license_name=self.commerce_connector.license_name,
            )
            self.store.finish_source_request(
                request_id=request_id,
                http_status=response.http_status,
                raw_content=response.raw_content,
            )
            for work in response.works:
                self._store_commerce_work(run_id=run_id, request_id=request_id, work=work)
            self._save_commerce_summary(run_id=run_id, works=response.works, target_market=target_market)
            if response.intel_brief_error:
                error_info = response.intel_brief_error
                intel_request_id = self.store.start_source_request(
                    research_run_id=run_id,
                    source="cli_market_intel",
                    request_url=error_info.get("request_url") or f"{self.commerce_connector.base_url}/v1/intel/brief",
                    request_params=error_info.get("request_params") or {"country": target_market, "line": line},
                    license_name=self.commerce_connector.license_name,
                )
                self.store.fail_source_request(
                    request_id=intel_request_id,
                    http_status=error_info.get("http_status"),
                    error=error_info.get("message", "CLI Market intel brief failed"),
                    raw_content=error_info.get("raw_content"),
                )
        except CLIMarketRequestError as error:
            if request_id is None:
                request_params = error.request_params or {"query": query, "country": target_market}
                request_url = error.request_url or self.commerce_connector.base_url
                request_id = self.store.start_source_request(
                    research_run_id=run_id,
                    source=self.commerce_connector.source,
                    request_url=request_url,
                    request_params=request_params,
                    license_name=self.commerce_connector.license_name,
                )
            self.store.fail_source_request(
                request_id=request_id,
                http_status=error.http_status,
                error=str(error),
                raw_content=error.raw_content,
            )
            raise ResearchExecutionError(run_id, str(error)) from error
        return self.store.get_run_detail(run_id)

    def _store_commerce_work(self, *, run_id: str, request_id: str, work: dict[str, Any]) -> None:
        external_id = str(work.get("external_id") or "").strip()
        title = str(work.get("title") or "").strip()
        if not external_id or not title:
            return
        normalized = {
            "external_id": external_id,
            "title": title,
            "best_price": work.get("best_price") or work.get("price"),
            "best_store": work.get("best_store") or work.get("store"),
            "brand": work.get("brand"),
            "prices": work.get("prices"),
            "country": work.get("country"),
            "brief": work.get("brief"),
            "source": work.get("source", "cli_market"),
        }
        self.store.add_evidence(
            research_run_id=run_id,
            source_request_id=request_id,
            source="cli_market",
            domain="commerce",
            external_id=external_id,
            title=title,
            published_at=None,
            geography=work.get("country"),
            payload=normalized,
            dedupe_key=f"cli_market:{external_id}".strip().casefold(),
        )

    def _save_commerce_summary(self, *, run_id: str, works: list[dict[str, Any]], target_market: str) -> None:
        prices: list[float] = []
        store_counter: Counter[str] = Counter()
        brand_counter: Counter[str] = Counter()
        brief_payload: dict[str, Any] | None = None
        for work in works:
            price = work.get("best_price") or work.get("price")
            if price is not None:
                try:
                    prices.append(float(price))
                except (TypeError, ValueError):
                    pass
            store = work.get("best_store") or work.get("store")
            if store:
                store_counter[str(store)] += 1
            brand = work.get("brand")
            if brand:
                brand_counter[str(brand)] += 1
            if work.get("brief"):
                brief_payload = work.get("brief")
        self.store.save_domain_summary(
            research_run_id=run_id,
            domain="commerce",
            summary_type="climarket_aggregation",
            payload={
                "target_market": target_market,
                "shelf_products_count": len([w for w in works if w.get("source") != "cli_market_intel"]),
                "stores_compared": len(store_counter),
                "price_min": min(prices) if prices else None,
                "price_max": max(prices) if prices else None,
                "price_avg": round(sum(prices) / len(prices), 2) if prices else None,
                "top_stores": [name for name, _ in store_counter.most_common(10)],
                "top_brands": [name for name, _ in brand_counter.most_common(10)],
                "intel_brief": brief_payload,
            },
        )

    def run_full_pipeline(
        self,
        *,
        query: str,
        target_market: str,
        application: str,
        cutoff_at: str,
        from_publication_date: str,
        limit: int,
        hs_code: str | None = None,
    ) -> dict[str, Any]:
        run = self.run_science_research(
            query=query,
            target_market=target_market,
            application=application,
            cutoff_at=cutoff_at,
            from_publication_date=from_publication_date,
            limit=limit,
        )
        run_id = run["id"]
        optional_steps = [
            ("crossref", lambda: self.enrich_with_crossref(run_id=run_id, limit=limit)),
            ("pubmed", lambda: self.enrich_with_pubmed(run_id=run_id, limit=limit)),
            ("semanticscholar", lambda: self.enrich_with_semanticscholar(run_id=run_id, limit=limit)),
            ("patent", lambda: self.enrich_with_patent(run_id=run_id, limit=limit)),
            ("trend", lambda: self.enrich_with_trend(run_id=run_id, limit=limit)),
            ("trade", lambda: self.enrich_with_trade(run_id=run_id, limit=limit, hs_code=hs_code)),
            ("commerce", lambda: self.enrich_with_commerce(run_id=run_id, limit=limit)),
            ("regulatory", lambda: self.enrich_with_regulatory(run_id=run_id, limit=limit)),
            ("sustainability", lambda: self.enrich_with_sustainability(run_id=run_id, limit=limit)),
            ("techscout", lambda: self.enrich_with_techscout(run_id=run_id, limit=limit)),
        ]
        pipeline_failures: list[str] = []
        for step_name, step in optional_steps:
            try:
                step()
            except ResearchExecutionError as error:
                pipeline_failures.append(f"{step_name}: {error}")
            except RuntimeError as error:
                if "not configured" in str(error).lower():
                    continue
                raise
        if pipeline_failures:
            self.store.save_domain_summary(
                research_run_id=run_id,
                domain="pipeline",
                summary_type="pipeline_warnings",
                payload={"failures": pipeline_failures},
            )
        return self.store.get_run_detail(run_id)

    def enrich_with_regulatory(self, *, run_id: str, limit: int) -> dict[str, Any]:
        run = self.store.get_run(run_id)
        query, from_date, target_market = _run_context(run)
        connectors = [
            ("openfda", self.openfda_connector, OpenFDARequestError),
            ("efsa_eurlex", self.efsa_connector, EFSALexRequestError),
            ("fooddata_central", self.fooddata_connector, FoodDataCentralRequestError),
        ]
        failures: list[str] = []
        for source, connector, error_cls in connectors:
            if connector is None:
                continue
            request_id: str | None = None
            try:
                response = connector.search(
                    query=query,
                    from_publication_date=from_date,
                    limit=limit,
                    target_market=target_market,
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
                failures.append(f"{connector.source}: {error}")
        self._save_regulatory_summary(run_id=run_id)
        if failures:
            raise ResearchExecutionError(run_id, "; ".join(failures))
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
        counts = self.store.count_evidence_by_source(run_id, "regulatory")
        sources = [{"source": row["source"], "record_count": row["count"]} for row in counts]
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
        query, from_date, _target_market = _run_context(run)
        request_id: str | None = None
        try:
            response = self.climatiq_connector.search(
                query=query,
                from_publication_date=from_date,
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
        query, from_date, _target_market = _run_context(run)
        connectors = [
            ("cordis", self.cordis_connector, CORDISRequestError),
            ("nih_reporter", self.nih_connector, NIHReporterRequestError),
            ("nsf_awards", self.nsf_connector, NSFAwardsRequestError),
        ]
        failures: list[str] = []
        for source, connector, error_cls in connectors:
            if connector is None:
                continue
            request_id: str | None = None
            try:
                response = connector.search(
                    query=query,
                    from_publication_date=from_date,
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
                failures.append(f"{connector.source}: {error}")
        self._save_techscout_summary(run_id=run_id)
        if failures:
            raise ResearchExecutionError(run_id, "; ".join(failures))
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
        counts = self.store.count_evidence_by_source(run_id, "technology_scout")
        sources = [{"source": row["source"], "project_count": row["count"]} for row in counts]
        self.store.save_domain_summary(
            research_run_id=run_id,
            domain="technology_scout",
            summary_type="techscout_aggregation",
            payload={
                "sources": sources,
                "total_projects": sum(s["project_count"] for s in sources),
            },
        )
