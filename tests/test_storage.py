from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pit.storage import ResearchStore


class StorageSecretRedactionTests(unittest.TestCase):
    """ResearchStore must never persist known-sensitive request params in the clear.

    This is a defense-in-depth backstop: even if a connector forgets to keep a
    secret out of its request_url/request_params (as fooddata_central.py once did),
    the store itself must not write it to disk or hand it back through get_run_detail.
    """

    def _store(self, directory: str) -> ResearchStore:
        return ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")

    def test_start_source_request_redacts_known_sensitive_param_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = self._store(directory)
            run = store.create_run(
                query_original="cocoa",
                query_normalized="cocoa",
                target_market="US",
                application="functional foods",
                cutoff_at="2026-07-24T00:00:00+00:00",
            )
            request_id = store.start_source_request(
                research_run_id=run["id"],
                source="fooddata_central",
                request_url="https://api.nal.usda.gov/fdc/v1/search?query=cocoa&api_key=super-secret-key",
                request_params={"query": "cocoa", "api_key": "super-secret-key"},
                license_name="FoodData Central; public domain",
            )
            store.finish_source_request(request_id=request_id, http_status=200, raw_content=b"{}")

            detail = store.get_run_detail(run["id"])
            source_row = next(s for s in detail["sources"] if s["id"] == request_id)

            self.assertNotIn("super-secret-key", source_row["request_url"])
            self.assertNotIn("super-secret-key", str(source_row["request_params"]))
            self.assertEqual(source_row["request_params"]["api_key"], "***REDACTED***")

    def test_start_source_request_leaves_non_sensitive_params_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = self._store(directory)
            run = store.create_run(
                query_original="cocoa",
                query_normalized="cocoa",
                target_market="US",
                application="functional foods",
                cutoff_at="2026-07-24T00:00:00+00:00",
            )
            request_id = store.start_source_request(
                research_run_id=run["id"],
                source="openalex",
                request_url="https://api.openalex.org/works?search=cocoa&per-page=10",
                request_params={"search": "cocoa", "per-page": "10"},
                license_name="OpenAlex data snapshot; attribution required",
            )
            store.finish_source_request(request_id=request_id, http_status=200, raw_content=b"{}")

            detail = store.get_run_detail(run["id"])
            source_row = next(s for s in detail["sources"] if s["id"] == request_id)

            self.assertEqual(source_row["request_params"], {"search": "cocoa", "per-page": "10"})
            self.assertEqual(
                source_row["request_url"],
                "https://api.openalex.org/works?search=cocoa&per-page=10",
            )


class StorageCountEvidenceBySourceTests(unittest.TestCase):
    """count_evidence_by_source is the public accessor regulatory/techscout summaries must use.

    research.py previously called db.execute() directly with a literal '?'
    placeholder, bypassing self.store._execute()'s Postgres translation
    (?, -> %s). This method is the fix: it goes through _execute like every
    other store method, so it works on both backends.
    """

    def _store(self, directory: str) -> ResearchStore:
        return ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")

    def test_counts_evidence_grouped_by_source_for_domain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = self._store(directory)
            run = store.create_run(
                query_original="cocoa",
                query_normalized="cocoa",
                target_market="US",
                application="functional foods",
                cutoff_at="2026-07-24T00:00:00+00:00",
            )
            request_id = store.start_source_request(
                research_run_id=run["id"],
                source="openfda",
                request_url="https://api.fda.gov/food/enforcement.json",
                request_params={"search": "cocoa"},
                license_name="openFDA; public domain",
            )
            store.finish_source_request(request_id=request_id, http_status=200, raw_content=b"{}")
            store.add_evidence(
                research_run_id=run["id"],
                source_request_id=request_id,
                source="openfda",
                domain="regulatory",
                external_id="REC-1",
                title="Recall 1",
                published_at=None,
                geography=None,
                payload={"status": "ongoing"},
                dedupe_key="openfda:rec-1",
            )
            store.add_evidence(
                research_run_id=run["id"],
                source_request_id=request_id,
                source="openfda",
                domain="regulatory",
                external_id="REC-2",
                title="Recall 2",
                published_at=None,
                geography=None,
                payload={"status": "ongoing"},
                dedupe_key="openfda:rec-2",
            )

            counts = store.count_evidence_by_source(run["id"], "regulatory")

            self.assertEqual(counts, [{"source": "openfda", "count": 2}])

    def test_counts_are_scoped_to_domain_and_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = self._store(directory)
            run = store.create_run(
                query_original="cocoa",
                query_normalized="cocoa",
                target_market="US",
                application="functional foods",
                cutoff_at="2026-07-24T00:00:00+00:00",
            )
            request_id = store.start_source_request(
                research_run_id=run["id"],
                source="cordis",
                request_url="https://cordis.europa.eu/search",
                request_params={"q": "cocoa"},
                license_name="CORDIS; CC BY 4.0",
            )
            store.finish_source_request(request_id=request_id, http_status=200, raw_content=b"{}")
            store.add_evidence(
                research_run_id=run["id"],
                source_request_id=request_id,
                source="cordis",
                domain="technology_scout",
                external_id="PROJ-1",
                title="Project 1",
                published_at=None,
                geography=None,
                payload={},
                dedupe_key="cordis:proj-1",
            )

            self.assertEqual(
                store.count_evidence_by_source(run["id"], "technology_scout"),
                [{"source": "cordis", "count": 1}],
            )
            self.assertEqual(store.count_evidence_by_source(run["id"], "regulatory"), [])

    def test_uses_the_placeholder_translation_helper_not_raw_db_execute(self) -> None:
        """Regression guard: force the postgres code path (no real connection needed,
        since _execute only rewrites the query string) and assert it doesn't blow up
        trying to run a literal '?' placeholder against a %s-style backend."""
        with tempfile.TemporaryDirectory() as directory:
            store = self._store(directory)
            run = store.create_run(
                query_original="cocoa",
                query_normalized="cocoa",
                target_market="US",
                application="functional foods",
                cutoff_at="2026-07-24T00:00:00+00:00",
            )

            captured_queries: list[str] = []
            original_execute = store._execute

            def spying_execute(connection, query, params=()):
                # Simulate the postgres placeholder translation without a real connection.
                translated = query.replace("?", "%s") if store._backend == "sqlite" else query
                captured_queries.append(translated)
                return original_execute(connection, query, params)

            store._execute = spying_execute  # type: ignore[method-assign]
            try:
                store.count_evidence_by_source(run["id"], "regulatory")
            finally:
                store._execute = original_execute  # type: ignore[method-assign]

            self.assertTrue(captured_queries, "count_evidence_by_source must go through self._execute")
            self.assertNotIn("?", captured_queries[0])


if __name__ == "__main__":
    unittest.main()
