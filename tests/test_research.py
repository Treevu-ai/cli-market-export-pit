from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from pit.api import create_app
from pit.comtrade import ComtradeResponse
from pit.cordis import CORDISResponse
from pit.crossref import CrossrefResponse
from pit.epo_ops import EPOOPSResponse
from pit.gdelt import GDELTResponse
from pit.nih_reporter import NIHReporterResponse
from pit.nsf_awards import NSFAwardsResponse
from pit.openalex import OpenAlexRequestError, OpenAlexResponse
from pit.openfda import OpenFDARequestError, OpenFDAResponse
from pit.efsa_eurlex import EFSALexResponse
from pit.fooddata_central import FoodDataCentralResponse
from pit.nih_reporter import NIHReporterRequestError
from pit.climatiq import ClimatiqResponse
from pit.climarket import CLIMarketResponse
from pit.pubmed import PubMedResponse
from pit.research import ResearchExecutionError, ResearchService, _crossref_publication_date
from pit.scoring import ScoringService
from pit.reports import ReportGenerator
from pit.semanticscholar import SemanticScholarRequestError, SemanticScholarResponse
from pit.storage import ResearchStore


class SuccessfulConnector:
    source = "openalex"
    license_name = "OpenAlex data snapshot; attribution required"
    base_url = "https://api.openalex.org/works"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> OpenAlexResponse:
        raw_content = b'{"results":[{"id":"W1"}]}'
        return OpenAlexResponse(
            request_url="https://api.openalex.org/works?search=cocoa",
            request_params={"search": query, "per-page": str(limit)},
            http_status=200,
            raw_content=raw_content,
            works=[
                {
                    "id": "https://openalex.org/W1",
                    "doi": "https://doi.org/10.1000/cocoa",
                    "title": "Cocoa flavanols in functional foods",
                    "publication_date": "2024-05-01",
                    "cited_by_count": 12,
                    "type": "article",
                },
                {
                    "id": "https://openalex.org/W2",
                    "doi": "https://doi.org/10.1000/cocoa",
                    "title": "Duplicate DOI is ignored",
                    "publication_date": "2024-05-02",
                    "cited_by_count": 3,
                    "type": "article",
                },
            ],
        )


class FailingConnector(SuccessfulConnector):
    def search(self, *, query: str, from_publication_date: str, limit: int) -> OpenAlexResponse:
        raise OpenAlexRequestError("OpenAlex returned HTTP 429", http_status=429, raw_content=b'{"error":"rate"}')


class SuccessfulCrossrefConnector:
    source = "crossref"
    license_name = "Crossref REST API metadata; attribution and etiquette required"
    base_url = "https://api.crossref.org/works"

    def search(self, *, query: str, limit: int) -> CrossrefResponse:
        return CrossrefResponse(
            request_url="https://api.crossref.org/works?query.bibliographic=cocoa",
            request_params={"query.bibliographic": query, "rows": str(limit)},
            http_status=200,
            raw_content=b'{"message":{"items":[{"DOI":"10.1000/cocoa"}]}}',
            works=[
                {
                    "DOI": "10.1000/cocoa",
                    "title": ["Cocoa flavanols in functional foods"],
                    "type": "journal-article",
                    "publisher": "Example publisher",
                    "published-online": {"date-parts": [[2024, 5, 1]]},
                    "URL": "https://doi.org/10.1000/cocoa",
                }
            ],
        )


class TestCrossrefPublicationDate(unittest.TestCase):
    def test_returns_none_when_year_is_null(self) -> None:
        work = {"issued": {"date-parts": [[None]]}}
        self.assertIsNone(_crossref_publication_date(work))

    def test_falls_back_to_next_key_when_year_is_null(self) -> None:
        work = {
            "published-online": {"date-parts": [[None]]},
            "issued": {"date-parts": [[2023, 6]]},
        }
        self.assertEqual(_crossref_publication_date(work), "2023-06-01")

    def test_defaults_missing_month_and_day_when_null(self) -> None:
        work = {"issued": {"date-parts": [[2022, None, None]]}}
        self.assertEqual(_crossref_publication_date(work), "2022-01-01")

    def test_returns_full_date_when_complete(self) -> None:
        work = {"published-print": {"date-parts": [[2021, 3, 15]]}}
        self.assertEqual(_crossref_publication_date(work), "2021-03-15")


class SuccessfulPubMedConnector:
    source = "pubmed"
    license_name = "NCBI E-utilities; public domain"
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> PubMedResponse:
        return PubMedResponse(
            request_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=cocoa",
            request_params={"db": "pubmed", "term": query, "retmax": str(limit)},
            http_status=200,
            raw_content=b'{"esearchresult":{"idlist":["12345","67890"]}}',
            works=[
                {
                    "pmid": "12345",
                    "title": "Cocoa flavanols health effects",
                    "publication_date": "2024-03-01",
                    "doi": "10.2000/cocoa",
                },
                {
                    "pmid": "67890",
                    "title": "Flavanols in functional foods",
                    "publication_date": "2024-04-01",
                    "doi": None,
                },
            ],
        )


class SuccessfulSemanticScholarConnector:
    source = "semanticscholar"
    license_name = "Semantic Scholar Open Data; attribution required"
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> SemanticScholarResponse:
        return SemanticScholarResponse(
            request_url="https://api.semanticscholar.org/graph/v1/paper/search?query=cocoa",
            request_params={"query": query, "limit": str(limit)},
            http_status=200,
            raw_content=b'{"data":[{"paperId":"abc","title":"Cocoa study","year":2024}]}',
            works=[
                {
                    "paper_id": "abc",
                    "title": "Cocoa study",
                    "publication_date": "2024-06-01",
                    "doi": "10.3000/cocoa",
                    "authors": [{"name": "Author A"}],
                    "citation_count": 5,
                }
            ],
        )


class FailingSemanticScholarConnector(SuccessfulSemanticScholarConnector):
    def search(self, *, query: str, from_publication_date: str, limit: int) -> SemanticScholarResponse:
        raise SemanticScholarRequestError(
            "Semantic Scholar returned HTTP 429",
            http_status=429,
            raw_content=b'{"error":"rate"}',
        )


class SuccessfulPatentConnector:
    source = "epo_ops"
    license_name = "EPO OPS; free tier with registration"
    base_url = "https://ops.epo.org/3.2/rest-services/search"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> EPOOPSResponse:
        return EPOOPSResponse(
            request_url="https://ops.epo.org/3.2/rest-services/search?q=cocoa",
            request_params={"q": query, "rows": str(limit)},
            http_status=200,
            raw_content=b'{"ops:searchResult":{"ops:result":[{"dc:identifier":"EP123","ops:title":"Cocoa patent","ops:applicants":{"ops:applicant":{"ops:name":"Nestle"}}}]}}',
            works=[
                {
                    "patent_number": "EP123",
                    "title": "Cocoa patent",
                    "assignees": ["Nestle"],
                    "ipc_codes": ["A23L"],
                    "publication_date": "2023-01-01",
                    "source": "epo_ops",
                },
                {
                    "patent_number": "EP456",
                    "title": "Cocoa process",
                    "assignees": ["DSM"],
                    "ipc_codes": ["C12N"],
                    "publication_date": "2024-01-01",
                    "source": "epo_ops",
                },
            ],
        )


class SuccessfulTrendConnector:
    source = "gdelt"
    license_name = "GDELT Project; open for non-commercial use"
    base_url = "https://api.gdeltproject.org/api/v2/doc/doc"

    def search(self, *, query: str, from_publication_date: str, limit: int, target_market: str | None = None) -> GDELTResponse:
        return GDELTResponse(
            request_url="https://api.gdeltproject.org/api/v2/doc/doc?query=cocoa",
            request_params={"query": query, "maxrecords": str(limit)},
            http_status=200,
            raw_content=b'{"articles":[{"url":"https://example.com/1","title":"Cocoa demand rises","date":"2024-01-01"},{"url":"https://example.com/2","title":"Cocoa market trends","date":"2024-02-01"}]}',
            works=[
                {
                    "url": "https://example.com/1",
                    "title": "Cocoa demand rises",
                    "publication_date": "2024-01-01",
                    "source": "gdelt",
                    "language": "en",
                    "domain": "example.com",
                },
                {
                    "url": "https://example.com/2",
                    "title": "Cocoa market trends",
                    "publication_date": "2024-02-01",
                    "source": "gdelt",
                    "language": "en",
                    "domain": "example.org",
                },
            ],
        )


class SuccessfulTradeConnector:
    source = "comtrade"
    license_name = "UN Comtrade; open data with attribution"
    base_url = "https://comtradeapi.un.org/getData"

    def search(self, *, query: str, from_publication_date: str, limit: int, hs_code: str | None = None, target_market: str | None = None) -> ComtradeResponse:
        return ComtradeResponse(
            request_url="https://comtradeapi.un.org/getData?query=cocoa",
            request_params={"query": query, "maxrecords": str(limit)},
            http_status=200,
            raw_content=b'{"data":[{"reporterDesc":"Peru","partnerDesc":"USA","flowDesc":"Export","period":2024,"tradeValue":1000000,"netWeight":5000,"cmdCode":"1806.10"}]}',
            works=[
                {
                    "reporter": "Peru",
                    "partner": "USA",
                    "flow": "Export",
                    "period": "2024",
                    "trade_value_usd": 1000000,
                    "net_weight_kg": 5000,
                    "hs_code": "1806.10",
                    "source": "comtrade",
                },
            ],
        )


class SuccessfulCORDISConnector:
    source = "cordis"
    license_name = "CORDIS Open Data; attribution required"
    base_url = "https://cordis.europa.eu/api/search"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> CORDISResponse:
        return CORDISResponse(
            request_url="https://cordis.europa.eu/api/search?query=cocoa",
            request_params={"query": query, "pageSize": str(limit)},
            http_status=200,
            raw_content=b'{"projects":{"project":[{"id":"CORDIS123","title":"Cocoa innovation project","startDate":"2023-01-01","endDate":"2025-12-31","fundingAmount":1000000,"currency":"EUR"}]}}',
            works=[
                {
                    "project_id": "CORDIS123",
                    "title": "Cocoa innovation project",
                    "start_date": "2023-01-01",
                    "end_date": "2025-12-31",
                    "funding_amount": 1000000,
                    "currency": "EUR",
                    "organizations": [],
                    "source": "cordis",
                },
            ],
        )


class SuccessfulNIHConnector:
    source = "nih_reporter"
    license_name = "NIH RePORTER; public data"
    base_url = "https://api.reporter.nih.gov/v2/projects/search"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> NIHReporterResponse:
        return NIHReporterResponse(
            request_url="https://api.reporter.nih.gov/v2/projects/search?query=cocoa",
            request_params={"query": query, "limit": str(limit)},
            http_status=200,
            raw_content=b'{"results":[{"project_number":"NIH456","project_title":"Cocoa health study","start_date":"2022-01-01","end_date":"2024-12-31","total_cost":500000}]}',
            works=[
                {
                    "project_id": "NIH456",
                    "title": "Cocoa health study",
                    "start_date": "2022-01-01",
                    "end_date": "2024-12-31",
                    "funding_amount": 500000,
                    "currency": "USD",
                    "organizations": [],
                    "source": "nih_reporter",
                },
            ],
        )


class FailingNIHConnector:
    source = "nih_reporter"
    license_name = "NIH RePORTER; public data"
    base_url = "https://api.reporter.nih.gov/v2/projects/search"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> NIHReporterResponse:
        raise NIHReporterRequestError(
            "NIH Reporter returned HTTP 500",
            http_status=500,
            raw_content=b'{"error":"internal"}',
        )


class SuccessfulNSFConnector:
    source = "nsf_awards"
    license_name = "NSF Open Data; public domain"
    base_url = "https://api.nsf.gov/services/v1/awards/search"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> NSFAwardsResponse:
        return NSFAwardsResponse(
            request_url="https://api.nsf.gov/services/v1/awards/search?keyword=cocoa",
            request_params={"keyword": query, "limit": str(limit)},
            http_status=200,
            raw_content=b'{"award":[{"id":"NSF789","title":"Cocoa sustainability research","startDate":"2021-01-01","expDate":"2023-12-31","amount":300000}]}',
            works=[
                {
                    "project_id": "NSF789",
                    "title": "Cocoa sustainability research",
                    "start_date": "2021-01-01",
                    "end_date": "2023-12-31",
                    "funding_amount": 300000,
                    "currency": "USD",
                    "organizations": [],
                    "source": "nsf_awards",
                },
            ],
        )


class SuccessfulClimatiqConnector:
    source = "climatiq"
    license_name = "Climatiq; commercial with attribution"
    base_url = "https://api.climatiq.io/v2/search"

    def search(self, *, query: str, from_publication_date: str, limit: int) -> ClimatiqResponse:
        return ClimatiqResponse(
            request_url="https://api.climatiq.io/v2/search?query=cocoa",
            request_params={"query": query, "limit": str(limit)},
            http_status=200,
            raw_content=b'{"data":[{"id":"ACT123","name":"Cocoa production","category":"Agriculture","unit":"kg","co2e_factor":0.5}]}',
            works=[
                {
                    "activity_id": "ACT123",
                    "name": "Cocoa production",
                    "category": "Agriculture",
                    "unit": "kg",
                    "co2e_factor": 0.5,
                    "source": "climatiq",
                },
            ],
        )


class SuccessfulOpenFDAConnector:
    source = "openfda"
    license_name = "OpenFDA; public data"
    base_url = "https://api.fda.gov/food/enforcement.json"

    def search(self, *, query: str, from_publication_date: str, limit: int, target_market: str | None = None) -> OpenFDAResponse:
        return OpenFDAResponse(
            request_url="https://api.fda.gov/food/enforcement.json?search=cocoa",
            request_params={"search": query, "limit": str(limit)},
            http_status=200,
            raw_content=b'{"results":[{"recall_number":"FDA123","status":"Completed","classification":"Class I","product_description":"Cocoa product","reason_for_recall":"Contamination"}]}',
            works=[
                {
                    "recall_number": "FDA123",
                    "status": "Completed",
                    "classification": "Class I",
                    "product_description": "Cocoa product",
                    "reason_for_recall": "Contamination",
                    "source": "openfda",
                },
            ],
        )


class FailingOpenFDAConnector:
    source = "openfda"
    license_name = "OpenFDA; public data"
    base_url = "https://api.fda.gov/food/enforcement.json"

    def search(self, *, query: str, from_publication_date: str, limit: int, target_market: str | None = None) -> OpenFDAResponse:
        raise OpenFDARequestError(
            "OpenFDA returned HTTP 500",
            http_status=500,
            raw_content=b'{"error":"internal"}',
        )


class SuccessfulEFSALexConnector:
    source = "efsa_eurlex"
    license_name = "EUR-Lex; open data with attribution"
    base_url = "https://eur-lex.europa.eu/search.html"

    def search(self, *, query: str, from_publication_date: str, limit: int, target_market: str | None = None) -> EFSALexResponse:
        return EFSALexResponse(
            request_url="https://eur-lex.europa.eu/search.html?search_text=cocoa",
            request_params={"search_text": query, "limit": str(limit)},
            http_status=200,
            raw_content=b'{"results":[{"celex_number":"32023R1234","title":"Cocoa regulation","date":"2023-01-01","type":"Regulation"}]}',
            works=[
                {
                    "celex_number": "32023R1234",
                    "title": "Cocoa regulation",
                    "date": "2023-01-01",
                    "type": "Regulation",
                    "source": "efsa_eurlex",
                },
            ],
        )


class SuccessfulFoodDataCentralConnector:
    source = "fooddata_central"
    license_name = "FoodData Central; public domain"
    base_url = "https://api.nal.usda.gov/fdc/v1/search"

    def search(self, *, query: str, from_publication_date: str, limit: int, target_market: str | None = None) -> FoodDataCentralResponse:
        return FoodDataCentralResponse(
            request_url="https://api.nal.usda.gov/fdc/v1/search?query=cocoa",
            request_params={"query": query, "pageSize": str(limit)},
            http_status=200,
            raw_content=b'{"foods":[{"fdcId":123,"description":"Cocoa beans","dataType":"Foundation"}]}',
            works=[
                {
                    "fdc_id": 123,
                    "title": "Cocoa beans",
                    "data_type": "Foundation",
                    "source": "fooddata_central",
                },
            ],
        )


class SuccessfulCLIMarketConnector:
    source = "cli_market"
    license_name = "CLI Market shelf data; attribution required"
    base_url = "https://cli-market-api.fly.dev"

    def search(self, *, query: str, from_publication_date: str, limit: int, target_market: str | None = None, line: str = "supermercados") -> CLIMarketResponse:
        return CLIMarketResponse(
            request_url="https://cli-market-api.fly.dev/products/compare",
            request_params={"query": query, "country": target_market or "US", "line": line, "limit": str(limit)},
            http_status=200,
            raw_content=b'{"comparison":[{"name":"Organic Blueberry 1lb","brand":"Fresh Farms","best_price":5.99,"best_store":"vitacost_us","prices":{"vitacost_us":5.99}}]}',
            works=[
                {
                    "external_id": "compare:0:organic blueberry 1lb",
                    "title": "Organic Blueberry 1lb",
                    "brand": "Fresh Farms",
                    "best_price": 5.99,
                    "best_store": "vitacost_us",
                    "prices": {"vitacost_us": 5.99},
                    "country": target_market or "US",
                    "source": "cli_market_compare",
                },
                {
                    "external_id": "brief:US:supermercados",
                    "title": "CLI Market intel brief (US/supermercados)",
                    "brief": {"pressure": "stable"},
                    "source": "cli_market_intel",
                },
            ],
        )


class ResearchServiceTests(unittest.TestCase):
    def _service(
        self,
        directory: str,
        connector,
        crossref_connector=None,
        pubmed_connector=None,
        semanticscholar_connector=None,
        patent_connector=None,
        trend_connector=None,
        trade_connector=None,
        cordis_connector=None,
        nih_connector=None,
        nsf_connector=None,
        openfda_connector=None,
        efsa_connector=None,
        fooddata_connector=None,
        climatiq_connector=None,
        commerce_connector=None,
    ) -> tuple[ResearchStore, ResearchService]:
        store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
        return store, ResearchService(
            store,
            connector,
            crossref_connector,
            pubmed_connector,
            semanticscholar_connector,
            patent_connector,
            trend_connector,
            trade_connector,
            cordis_connector,
            nih_connector,
            nsf_connector,
            openfda_connector,
            efsa_connector,
            fooddata_connector,
            climatiq_connector,
            commerce_connector,
        )

    def test_persists_immutable_raw_response_and_normalized_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(directory, SuccessfulConnector())
            result = service.run_science_research(
                query=" High-Flavanol   Cocoa Powder ",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["query_normalized"], "high-flavanol cocoa powder")
            self.assertEqual(len(result["evidence"]), 1)
            self.assertEqual(result["evidence"][0]["domain"], "science")
            source = result["sources"][0]
            self.assertEqual(source["status"], "completed")
            self.assertEqual(source["checksum"], hashlib.sha256(b'{"results":[{"id":"W1"}]}').hexdigest())
            self.assertEqual((Path(directory) / "raw" / source["raw_object_key"]).read_bytes(), b'{"results":[{"id":"W1"}]}')

    def test_surfaces_connector_failure_and_marks_run_failed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(directory, FailingConnector())

            with self.assertRaises(ResearchExecutionError) as raised:
                service.run_science_research(
                    query="cocoa powder",
                    target_market="US",
                    application="functional foods and beverages",
                    cutoff_at="2026-07-24T00:00:00+00:00",
                    from_publication_date="2021-01-01",
                    limit=10,
                )

            detail = store.get_run_detail(raised.exception.run_id)
            self.assertEqual(detail["status"], "failed")
            self.assertEqual(detail["sources"][0]["http_status"], 429)
            self.assertEqual(detail["sources"][0]["status"], "failed")
            self.assertEqual(detail["sources"][0]["request_params"]["search"], "cocoa powder")
            self.assertEqual(detail["sources"][0]["request_params"]["filter"], "from_publication_date:2021-01-01")
            self.assertEqual(detail["sources"][0]["request_params"]["per-page"], "10")
            self.assertTrue((Path(directory) / "raw" / detail["sources"][0]["raw_object_key"]).exists())

    def test_api_creates_and_returns_a_traceable_research_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, service = self._service(directory, SuccessfulConnector())
            client = TestClient(create_app(service))

            created = client.post(
                "/v1/research-runs",
                json={"query": "high-flavanol cocoa powder", "limit": 10},
            )

            self.assertEqual(created.status_code, 201)
            body = created.json()
            self.assertEqual(body["data"]["status"], "completed")
            self.assertEqual(body["meta"]["evidence_count"], 1)
            self.assertIn("timestamp", body["trace"])

            fetched = client.get(f"/v1/research-runs/{body['data']['id']}")
            self.assertEqual(fetched.status_code, 200)
            self.assertEqual(fetched.json()["data"]["sources"][0]["source"], "openalex")

    def test_crossref_enrichment_links_matching_doi_without_duplicate_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, service = self._service(
                directory,
                SuccessfulConnector(),
                SuccessfulCrossrefConnector(),
            )
            initial = service.run_science_research(
                query="high-flavanol cocoa powder",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )

            enriched = service.enrich_with_crossref(run_id=initial["id"], limit=10)

            self.assertEqual(len(enriched["evidence"]), 1)
            self.assertEqual(len(enriched["sources"]), 2)
            self.assertEqual(
                {link["source"] for link in enriched["evidence"][0]["source_links"]},
                {"openalex", "crossref"},
            )

    def test_health_endpoint_returns_ok(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, service = self._service(directory, SuccessfulConnector())
            client = TestClient(create_app(service))
            response = client.get("/v1/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "ok")

    def test_pubmed_enrichment_stores_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(
                directory,
                SuccessfulConnector(),
                crossref_connector=SuccessfulCrossrefConnector(),
                pubmed_connector=SuccessfulPubMedConnector(),
            )
            initial = service.run_science_research(
                query="high-flavanol cocoa powder",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            enriched = service.enrich_with_pubmed(run_id=initial["id"], limit=10)
            pubmed_evidence = [e for e in enriched["evidence"] if e["source"] == "pubmed"]
            self.assertEqual(len(pubmed_evidence), 2)
            pubmed_ids = {e["external_id"] for e in pubmed_evidence}
            self.assertEqual(pubmed_ids, {"12345", "67890"})

    def test_semantic_scholar_enrichment_stores_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(
                directory,
                SuccessfulConnector(),
                crossref_connector=SuccessfulCrossrefConnector(),
                semanticscholar_connector=SuccessfulSemanticScholarConnector(),
            )
            initial = service.run_science_research(
                query="high-flavanol cocoa powder",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            enriched = service.enrich_with_semanticscholar(run_id=initial["id"], limit=10)
            ss_evidence = [e for e in enriched["evidence"] if e["source"] == "semanticscholar"]
            self.assertEqual(len(ss_evidence), 1)
            self.assertEqual(ss_evidence[0]["external_id"], "abc")

    def test_cache_avoids_duplicate_raw_storage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(directory, SuccessfulConnector())
            service.run_science_research(
                query="high-flavanol cocoa powder",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            raw_files = list((Path(directory) / "raw").glob("*.json"))
            initial_count = len(raw_files)
            service.run_science_research(
                query="high-flavanol cocoa powder",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            raw_files = list((Path(directory) / "raw").glob("*.json"))
            self.assertEqual(len(raw_files), initial_count)

    def test_domain_summaries_saved_with_top_entities(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(directory, SuccessfulConnector())
            result = service.run_science_research(
                query="high-flavanol cocoa powder",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            summaries = result.get("summaries", {})
            self.assertIn("openalex_aggregation", summaries)

    def test_taxonomy_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            taxonomy = store.create_taxonomy(name="cacao-functional", version="v2")
            self.assertIn("id", taxonomy)
            fetched = store.get_taxonomy(name="cacao-functional", version="v2")
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched["id"], taxonomy["id"])

    def test_patent_enrichment_stores_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(
                directory,
                SuccessfulConnector(),
                patent_connector=SuccessfulPatentConnector(),
            )
            initial = service.run_science_research(
                query="cocoa",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            enriched = service.enrich_with_patent(run_id=initial["id"], limit=10)
            patent_evidence = [e for e in enriched["evidence"] if e["domain"] == "patent"]
            self.assertEqual(len(patent_evidence), 2)
            patent_ids = {e["external_id"] for e in patent_evidence}
            self.assertEqual(patent_ids, {"EP123", "EP456"})
            summaries = enriched.get("summaries", {})
            self.assertIn("epo_ops_aggregation", summaries)
            self.assertEqual(summaries["epo_ops_aggregation"]["patents_count"], 2)
            self.assertEqual(summaries["epo_ops_aggregation"]["top_assignees"], ["Nestle", "DSM"])

    def test_trend_enrichment_stores_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(
                directory,
                SuccessfulConnector(),
                trend_connector=SuccessfulTrendConnector(),
            )
            initial = service.run_science_research(
                query="cocoa",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            enriched = service.enrich_with_trend(run_id=initial["id"], limit=10)
            trend_evidence = [e for e in enriched["evidence"] if e["domain"] == "trend"]
            self.assertEqual(len(trend_evidence), 2)
            urls = {e["external_id"] for e in trend_evidence}
            self.assertEqual(urls, {"https://example.com/1", "https://example.com/2"})
            summaries = enriched.get("summaries", {})
            self.assertIn("gdelt_aggregation", summaries)
            self.assertEqual(summaries["gdelt_aggregation"]["news_volume"], 2)

    def test_trade_enrichment_stores_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(
                directory,
                SuccessfulConnector(),
                trade_connector=SuccessfulTradeConnector(),
            )
            initial = service.run_science_research(
                query="cocoa",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            enriched = service.enrich_with_trade(run_id=initial["id"], limit=10)
            trade_evidence = [e for e in enriched["evidence"] if e["domain"] == "trade"]
            self.assertEqual(len(trade_evidence), 1)
            self.assertEqual(trade_evidence[0]["external_id"], "Peru-USA-2024-1806.10")
            summaries = enriched.get("summaries", {})
            self.assertIn("comtrade_aggregation", summaries)
            self.assertEqual(summaries["comtrade_aggregation"]["trade_records_count"], 1)

    def test_scoring_calculates_opportunity_and_saves_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(
                directory,
                SuccessfulConnector(),
                patent_connector=SuccessfulPatentConnector(),
                trend_connector=SuccessfulTrendConnector(),
                trade_connector=SuccessfulTradeConnector(),
            )
            initial = service.run_science_research(
                query="cocoa",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            service.enrich_with_patent(run_id=initial["id"], limit=10)
            service.enrich_with_trend(run_id=initial["id"], limit=10)
            service.enrich_with_trade(run_id=initial["id"], limit=10)
            scoring = ScoringService(store)
            scores = scoring.calculate_scores(initial["id"])
            self.assertIn("opportunity_score", scores)
            self.assertIn("recommendation", scores)
            claims = store.get_claims(initial["id"])
            self.assertTrue(len(claims) >= 1)

    def test_report_endpoint_returns_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(
                directory,
                SuccessfulConnector(),
                patent_connector=SuccessfulPatentConnector(),
                trend_connector=SuccessfulTrendConnector(),
                trade_connector=SuccessfulTradeConnector(),
            )
            initial = service.run_science_research(
                query="cocoa",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            scoring = ScoringService(store)
            scoring.calculate_scores(initial["id"])
            client = TestClient(create_app(service, scoring, ReportGenerator()))
            report = client.get(f"/v1/research-runs/{initial['id']}/report")
            self.assertEqual(report.status_code, 200)
            body = report.json()
            self.assertIn("run_id", body["data"])

    def test_connectors_status_returns_stats(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, service = self._service(directory, SuccessfulConnector())
            service.run_science_research(
                query="cocoa",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            client = TestClient(create_app(service))
            response = client.get("/v1/connectors/status")
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertIn("stats", body)
            self.assertIn("freshness", body)
            self.assertIn("quota", body)
            self.assertIn("metrics", body)

    def test_api_key_required_when_set(self) -> None:
        import os
        os.environ["PIT_API_KEY"] = "secret123"
        try:
            with tempfile.TemporaryDirectory() as directory:
                _, service = self._service(directory, SuccessfulConnector())
                client = TestClient(create_app(service))
                response = client.get("/v1/health")
                self.assertEqual(response.status_code, 401)
                response = client.get("/v1/health", headers={"X-API-Key": "secret123"})
                self.assertEqual(response.status_code, 200)
        finally:
            os.environ.pop("PIT_API_KEY", None)

    def test_techscout_enrichment_stores_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(
                directory,
                SuccessfulConnector(),
                cordis_connector=SuccessfulCORDISConnector(),
                nih_connector=SuccessfulNIHConnector(),
                nsf_connector=SuccessfulNSFConnector(),
            )
            initial = service.run_science_research(
                query="cocoa",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            enriched = service.enrich_with_techscout(run_id=initial["id"], limit=10)
            tech_evidence = [e for e in enriched["evidence"] if e["domain"] == "technology_scout"]
            self.assertEqual(len(tech_evidence), 3)
            sources = {e["source"] for e in tech_evidence}
            self.assertEqual(sources, {"cordis", "nih_reporter", "nsf_awards"})
            summaries = enriched.get("summaries", {})
            self.assertIn("techscout_aggregation", summaries)
            self.assertEqual(summaries["techscout_aggregation"]["total_projects"], 3)

    def test_techscout_summary_is_saved_even_when_one_connector_fails(self) -> None:
        """Regression: previously the aggregated summary was only saved when ALL
        techscout connectors succeeded, silently discarding evidence already
        stored by the ones that did succeed."""
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(
                directory,
                SuccessfulConnector(),
                cordis_connector=SuccessfulCORDISConnector(),
                nih_connector=FailingNIHConnector(),
                nsf_connector=SuccessfulNSFConnector(),
            )
            initial = service.run_science_research(
                query="cocoa",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )

            with self.assertRaises(ResearchExecutionError):
                service.enrich_with_techscout(run_id=initial["id"], limit=10)

            detail = store.get_run_detail(initial["id"])
            tech_evidence = [e for e in detail["evidence"] if e["domain"] == "technology_scout"]
            self.assertEqual({e["source"] for e in tech_evidence}, {"cordis", "nsf_awards"})

            summaries = detail.get("summaries", {})
            self.assertIn("techscout_aggregation", summaries)
            self.assertEqual(summaries["techscout_aggregation"]["total_projects"], 2)
            self.assertEqual(
                {s["source"] for s in summaries["techscout_aggregation"]["sources"]},
                {"cordis", "nsf_awards"},
            )

    def test_regulatory_enrichment_stores_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(
                directory,
                SuccessfulConnector(),
                openfda_connector=SuccessfulOpenFDAConnector(),
                efsa_connector=SuccessfulEFSALexConnector(),
                fooddata_connector=SuccessfulFoodDataCentralConnector(),
            )
            initial = service.run_science_research(
                query="cocoa",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            enriched = service.enrich_with_regulatory(run_id=initial["id"], limit=10)
            reg_evidence = [e for e in enriched["evidence"] if e["domain"] == "regulatory"]
            self.assertEqual(len(reg_evidence), 3)
            sources = {e["source"] for e in reg_evidence}
            self.assertEqual(sources, {"openfda", "efsa_eurlex", "fooddata_central"})
            summaries = enriched.get("summaries", {})
            self.assertIn("regulatory_aggregation", summaries)
            self.assertEqual(summaries["regulatory_aggregation"]["total_records"], 3)

    def test_regulatory_summary_is_saved_even_when_one_connector_fails(self) -> None:
        """Regression: previously the aggregated summary was only saved when ALL
        regulatory connectors succeeded, silently discarding evidence already
        stored by the ones that did succeed."""
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(
                directory,
                SuccessfulConnector(),
                openfda_connector=FailingOpenFDAConnector(),
                efsa_connector=SuccessfulEFSALexConnector(),
                fooddata_connector=SuccessfulFoodDataCentralConnector(),
            )
            initial = service.run_science_research(
                query="cocoa",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )

            with self.assertRaises(ResearchExecutionError):
                service.enrich_with_regulatory(run_id=initial["id"], limit=10)

            detail = store.get_run_detail(initial["id"])
            reg_evidence = [e for e in detail["evidence"] if e["domain"] == "regulatory"]
            self.assertEqual({e["source"] for e in reg_evidence}, {"efsa_eurlex", "fooddata_central"})

            summaries = detail.get("summaries", {})
            self.assertIn("regulatory_aggregation", summaries)
            self.assertEqual(summaries["regulatory_aggregation"]["total_records"], 2)
            self.assertEqual(
                {s["source"] for s in summaries["regulatory_aggregation"]["sources"]},
                {"efsa_eurlex", "fooddata_central"},
            )

    def test_sustainability_enrichment_stores_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store, service = self._service(
                directory,
                SuccessfulConnector(),
                climatiq_connector=SuccessfulClimatiqConnector(),
            )
            initial = service.run_science_research(
                query="cocoa",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            enriched = service.enrich_with_sustainability(run_id=initial["id"], limit=10)
            sust_evidence = [e for e in enriched["evidence"] if e["domain"] == "sustainability"]
            self.assertEqual(len(sust_evidence), 1)
            self.assertEqual(sust_evidence[0]["external_id"], "ACT123")
            summaries = enriched.get("summaries", {})
            self.assertIn("climatiq_aggregation", summaries)
            self.assertEqual(summaries["climatiq_aggregation"]["activity_count"], 1)


    def test_commerce_enrichment_stores_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, service = self._service(
                directory,
                SuccessfulConnector(),
                commerce_connector=SuccessfulCLIMarketConnector(),
            )
            initial = service.run_science_research(
                query="organic blueberry",
                target_market="US",
                application="fresh fruit export",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            enriched = service.enrich_with_commerce(run_id=initial["id"], limit=10)
            commerce_evidence = [e for e in enriched["evidence"] if e["domain"] == "commerce"]
            self.assertEqual(len(commerce_evidence), 2)
            summaries = enriched.get("summaries", {})
            self.assertIn("climarket_aggregation", summaries)
            self.assertEqual(summaries["climarket_aggregation"]["shelf_products_count"], 1)

    def test_full_pipeline_endpoint_runs_science_step(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, service = self._service(directory, SuccessfulConnector())
            client = TestClient(create_app(service))
            response = client.post(
                "/v1/research-runs/full",
                json={"query": "high-flavanol cocoa powder", "limit": 10},
            )
            self.assertEqual(response.status_code, 201)
            body = response.json()
            self.assertEqual(body["data"]["status"], "completed")
            self.assertGreaterEqual(len(body["data"]["sources"]), 1)

    def test_full_pipeline_continues_when_semanticscholar_rate_limited(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, service = self._service(
                directory,
                SuccessfulConnector(),
                semanticscholar_connector=FailingSemanticScholarConnector(),
            )
            run = service.run_full_pipeline(
                query="high-flavanol cocoa powder",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-26T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            self.assertEqual(run["status"], "completed")
            self.assertIn("pipeline_warnings", run.get("summaries", {}))
            failures = run["summaries"]["pipeline_warnings"]["failures"]
            self.assertTrue(any("semanticscholar" in item for item in failures))

    def test_enrich_endpoint_crossref(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, service = self._service(
                directory,
                SuccessfulConnector(),
                crossref_connector=SuccessfulCrossrefConnector(),
            )
            initial = service.run_science_research(
                query="high-flavanol cocoa powder",
                target_market="US",
                application="functional foods and beverages",
                cutoff_at="2026-07-24T00:00:00+00:00",
                from_publication_date="2021-01-01",
                limit=10,
            )
            client = TestClient(create_app(service))
            response = client.post(
                f"/v1/research-runs/{initial['id']}/enrich/crossref",
                json={"limit": 10},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()["data"]["sources"]), 2)


if __name__ == "__main__":
    unittest.main()
