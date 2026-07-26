#!/usr/bin/env python3
"""Demo end-to-end: arándano orgánico → mercado US."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from pit.reports import ReportGenerator
from pit.research import ResearchService
from pit.scoring import ScoringService
from pit.storage import ResearchStore
from pit.openalex import OpenAlexConnector
from pit.crossref import CrossrefConnector
from pit.pubmed import PubMedConnector
from pit.semanticscholar import SemanticScholarConnector
from pit.gdelt import GDELTConnector
from pit.comtrade import ComtradeConnector
from pit.openfda import OpenFDAConnector
from pit.efsa_eurlex import EFSALexConnector
from pit.fooddata_central import FoodDataCentralConnector
from pit.climarket import CLIMarketConnector
from pit.cordis import CORDISConnector
from pit.nih_reporter import NIHReporterConnector
from pit.nsf_awards import NSFAwardsConnector


def main() -> int:
    output_dir = Path(os.getenv("PIT_DEMO_DIR", tempfile.mkdtemp(prefix="pit-demo-")))
    store = ResearchStore(output_dir / "pit.db", output_dir / "raw")
    service = ResearchService(
        store,
        OpenAlexConnector(),
        CrossrefConnector(os.getenv("PIT_CONTACT_EMAIL")),
        PubMedConnector(),
        SemanticScholarConnector(),
        None,
        GDELTConnector(),
        ComtradeConnector(),
        CORDISConnector(),
        NIHReporterConnector(),
        NSFAwardsConnector(),
        OpenFDAConnector(),
        EFSALexConnector(),
        FoodDataCentralConnector(api_key=os.getenv("FOODDATA_CENTRAL_API_KEY")),
        None,
        CLIMarketConnector(),
    )
    scoring = ScoringService(store)
    report_gen = ReportGenerator()

    print("PIT demo: arándano orgánico → US")
    print(f"Output: {output_dir}")
    try:
        run = service.run_full_pipeline(
            query="organic blueberry",
            target_market="US",
            application="fresh and frozen fruit export",
            cutoff_at="2026-01-01T00:00:00+00:00",
            from_publication_date="2021-01-01",
            limit=10,
        )
    except Exception as error:
        print(f"Pipeline error (partial data may exist): {error}", file=sys.stderr)
        runs = list((output_dir / "raw").glob("*.json"))
        if not runs:
            return 1
        raise

    scores = scoring.calculate_scores(run["id"])
    report = report_gen.generate_json(run=run, scores=scores, domain_scores=scoring.build_domain_scores(run["id"]))
    report_path = output_dir / "arandano_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    pdf_path = output_dir / "arandano_report.pdf"
    pdf_path.write_bytes(report_gen.generate_pdf(run=run, scores=scores))

    print(f"Run ID: {run['id']}")
    print(f"Evidence: {len(run.get('evidence', []))}")
    print(f"Recommendation: {scores['recommendation']} (score {scores['opportunity_score']})")
    print(f"JSON: {report_path}")
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
