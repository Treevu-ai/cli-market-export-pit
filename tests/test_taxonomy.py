from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pitchavi.storage import ResearchStore
from pitchavi.taxonomy import ensure_default_taxonomy, resolve_hs_code


class TaxonomyTests(unittest.TestCase):
    def test_resolve_hs_code_for_cocoa(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pitchavi.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="high-flavanol cocoa powder",
            )
            self.assertEqual(hs, "180610")

    def test_resolve_hs_code_for_blueberry_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pitchavi.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="arandano organico",
            )
            self.assertEqual(hs, "081040")


if __name__ == "__main__":
    unittest.main()
