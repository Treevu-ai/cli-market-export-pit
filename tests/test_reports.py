from __future__ import annotations

import unittest

from pit.improvement_checklist import build_improvement_checklist, pdf_safe_text
from pit.reports import ReportGenerator


class ImprovementChecklistTests(unittest.TestCase):
    def test_suggests_epo_when_patent_data_missing(self) -> None:
        items = build_improvement_checklist(
            summaries={"openalex_aggregation": {"works_count": 3}},
            scores={
                "coverage_factor": 0.4,
                "recommendation": "Insufficient evidence",
                "alerts": [],
            },
            domain_scores=[
                {"domain": "science", "score": 30, "coverage": 0.9, "weight": 0.25},
                {"domain": "patent", "score": 0, "coverage": 0.0, "weight": 0.15},
            ],
        )
        titles = " ".join(item["title"] for item in items)
        self.assertIn("Cobertura insuficiente", titles)
        self.assertTrue(any("EPO" in item["action"] for item in items))

    def test_detects_semantic_scholar_rate_limit_alert(self) -> None:
        items = build_improvement_checklist(
            summaries={},
            scores={
                "coverage_factor": 0.7,
                "recommendation": "Validate",
                "alerts": ["Semantic Scholar returned HTTP 429"],
            },
            domain_scores=[],
        )
        self.assertTrue(any("SEMANTICSCHOLAR_API_KEY" in item["action"] for item in items))

    def test_pdf_safe_text_strips_accents(self) -> None:
        self.assertEqual(pdf_safe_text("Regulación y café"), "Regulacion y cafe")


class ReportGeneratorTests(unittest.TestCase):
    def test_generate_pdf_returns_bytes(self) -> None:
        run = {
            "id": "rr_test123",
            "query_original": "cacao alto flavanol",
            "target_market": "US",
            "application": "alimentos funcionales",
            "cutoff_at": "2026-07-27T00:00:00+00:00",
            "summaries": {
                "openalex_aggregation": {"works_count": 5},
                "regulatory_aggregation": {"total_records": 2},
            },
            "sources": [],
        }
        scores = {
            "score_version": "v1.0-mvp",
            "opportunity_score": 62.5,
            "coverage_factor": 0.72,
            "recommendation": "Validate",
            "alerts": [],
            "exclusions": [],
            "claims": [
                {"domain": "science", "statement": "Science score", "value": 50},
            ],
        }
        domain_scores = [
            {"domain": "science", "score": 50, "confidence": "high", "weight": 0.25, "coverage": 0.9},
            {"domain": "patent", "score": 0, "confidence": "medium", "weight": 0.15, "coverage": 0.0},
        ]
        pdf = ReportGenerator().generate_pdf(run=run, scores=scores, domain_scores=domain_scores)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 500)

    def test_generate_json_includes_checklist(self) -> None:
        run = {
            "id": "rr_test123",
            "query_original": "palta hass",
            "target_market": "US",
            "application": "fresh produce",
            "cutoff_at": "2026-07-27T00:00:00+00:00",
            "summaries": {},
            "sources": [],
        }
        scores = {
            "score_version": "v1.0-mvp",
            "opportunity_score": 20.0,
            "coverage_factor": 0.3,
            "recommendation": "Insufficient evidence",
            "alerts": [],
            "exclusions": [],
        }
        report = ReportGenerator().generate_json(run=run, scores=scores, domain_scores=[])
        self.assertIn("improvement_checklist", report)
        self.assertTrue(len(report["improvement_checklist"]) >= 1)


if __name__ == "__main__":
    unittest.main()
