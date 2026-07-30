from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from test_research import SuccessfulConnector

from pit.api import create_app
from pit.reports import ReportGenerator
from pit.research import ResearchService
from pit.scoring import ScoringService
from pit.storage import ResearchStore


class PublicExampleReportTests(unittest.TestCase):
    """Regression: /report/ with no run_id showed nothing at all -- there
    was no unauthenticated way to view any report, and every real report
    route requires a logged-in owner (Depends(get_current_user) +
    ownership check). Added one hardcoded public example run instead of a
    general auth bypass."""

    def setUp(self) -> None:
        directory = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
        service = ResearchService(store, SuccessfulConnector())
        scoring = ScoringService(store)
        self.client = TestClient(create_app(service, scoring, ReportGenerator()))
        run = service.run_science_research(
            user_id="system-example",
            query="cacao alto flavanol",
            target_market="EU",
            application="alimentos funcionales",
            cutoff_at="2026-07-30T00:00:00+00:00",
            from_publication_date="2020-01-01",
            limit=5,
        )
        scoring.calculate_scores(run["id"])
        self.run_id = run["id"]

    def test_returns_report_with_no_authentication(self) -> None:
        with patch("pit.api.EXAMPLE_REPORT_RUN_ID", self.run_id):
            response = self.client.get("/v1/public/example-report")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("data", body)
        self.assertEqual(body["data"]["query"], "cacao alto flavanol")

    def test_does_not_require_authorization_header(self) -> None:
        with patch("pit.api.EXAMPLE_REPORT_RUN_ID", self.run_id):
            response = self.client.get("/v1/public/example-report", headers={})

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
