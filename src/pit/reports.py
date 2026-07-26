"""Report generators for JSON and PDF exports."""

from __future__ import annotations

import json
from typing import Any


class ReportGenerator:
    def generate_json(self, run: dict[str, Any], scores: dict[str, Any], domain_scores: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return {
            "run_id": run["id"],
            "query": run["query_original"],
            "target_market": run["target_market"],
            "application": run["application"],
            "cutoff_at": run["cutoff_at"],
            "score": {
                "score_version": scores["score_version"],
                "opportunity_score": scores["opportunity_score"],
                "coverage_factor": scores["coverage_factor"],
                "recommendation": scores["recommendation"],
                "dimensions": {item["domain"]: {"score": item["score"], "confidence": item["confidence"], "weight": item["weight"], "coverage": item["coverage"]} for item in (domain_scores or [])},
                "alerts": scores["alerts"],
                "exclusions": scores["exclusions"],
            },
            "evidence_summary": {
                domain: summary
                for domain, summary in run.get("summaries", {}).items()
            },
            "claims": scores.get("claims", []),
            "sources": [
                {
                    "source": s["source"],
                    "request_url": s["request_url"],
                    "checksum": s["checksum"],
                    "status": s["status"],
                }
                for s in run.get("sources", [])
            ],
        }

    def generate_pdf(self, run: dict[str, Any], scores: dict[str, Any]) -> bytes:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, "PIT Research Report", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(200, 10, f"Run: {run['id']}", ln=True)
        pdf.cell(200, 10, f"Query: {run['query_original']}", ln=True)
        pdf.cell(200, 10, f"Score: {scores['opportunity_score']} ({scores['recommendation']})", ln=True)
        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "Evidence Summary", ln=True)
        pdf.set_font("Arial", "", 12)
        for domain, summary in run.get("summaries", {}).items():
            pdf.cell(200, 10, f"- {domain}: {json.dumps(summary)}", ln=True)
        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "Claims", ln=True)
        pdf.set_font("Arial", "", 12)
        for claim in scores.get("claims", []):
            pdf.cell(200, 10, f"- [{claim['domain']}] {claim['statement']}", ln=True)
        return pdf.output(dest="S").encode("latin-1")
