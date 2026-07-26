from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.product_intelligence.adapters.pit_context import (  # noqa: E402
    PITClient,
    build_context_bundle,
)


class PITContextAdapterTests(unittest.TestCase):
    def test_build_context_bundle_maps_aggregations(self) -> None:
        report = {
            "query": "blueberry",
            "target_market": "US",
            "application": "functional foods",
            "cutoff_at": "2026-07-26T00:00:00Z",
            "score": {
                "recommendation": "Investigate",
                "opportunity_score": 72.5,
                "coverage_factor": 0.85,
                "dimensions": {"science": {"score": 80}},
            },
            "evidence_summary": {
                "openalex_aggregation": {"works_count": 12},
                "climarket_aggregation": {"shelf_products_count": 4},
                "regulatory_aggregation": {"total_records": 2},
            },
            "claims": [],
            "sources": [],
        }

        bundle = build_context_bundle(run_id="run-123", report=report)

        self.assertEqual(bundle.run_id, "run-123")
        self.assertEqual(bundle.scientific["aggregations"]["openalex_aggregation"]["works_count"], 12)
        self.assertEqual(bundle.market["aggregations"]["climarket_aggregation"]["shelf_products_count"], 4)
        self.assertEqual(bundle.regulatory["aggregations"]["regulatory_aggregation"]["total_records"], 2)
        self.assertEqual(bundle.scientific["pit_recommendation"], "Investigate")

    def test_build_context_bundle_marks_missing_domains(self) -> None:
        report = {
            "query": "quinoa",
            "target_market": "PE",
            "score": {},
            "evidence_summary": {"openalex_aggregation": {"works_count": 1}},
            "claims": [],
            "sources": [],
        }
        bundle = build_context_bundle(run_id="run-456", report=report)
        self.assertEqual(bundle.market["status"], "insufficient_evidence")
        self.assertIn("climarket_aggregation", " ".join(bundle.market.get("vacios_criticos", [])))

    def test_infer_market_code(self) -> None:
        from agents.product_intelligence.runner import _infer_market_code

        self.assertEqual(_infer_market_code("PE"), "PE")
        self.assertEqual(_infer_market_code("Perú"), "PE")
        self.assertEqual(_infer_market_code("Estados Unidos"), "US")


class PITClientURLTests(unittest.TestCase):
    def test_client_strips_trailing_slash(self) -> None:
        client = PITClient("http://localhost:8000/")
        self.assertEqual(client.base_url, "http://localhost:8000")


if __name__ == "__main__":
    unittest.main()
