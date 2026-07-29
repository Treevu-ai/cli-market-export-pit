from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pit.storage import ResearchStore
from pit.taxonomy import ensure_default_taxonomy, resolve_hs_code


class TaxonomyTests(unittest.TestCase):
    def test_resolve_hs_code_for_cocoa(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="high-flavanol cocoa powder",
            )
            self.assertEqual(hs, "180610")

    def test_resolve_hs_code_for_blueberry_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="arandano organico",
            )
            self.assertEqual(hs, "081040")

    def test_resolve_hs_code_for_avocado_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="palta hass exportacion",
            )
            self.assertEqual(hs, "080440")

    def test_resolve_hs_code_for_mango(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="mango kent",
            )
            self.assertEqual(hs, "080450")

    def test_resolve_hs_code_for_mandarin_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="mandarina w murcott",
            )
            self.assertEqual(hs, "080520")

    def test_resolve_hs_code_for_tangerine_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="fresh tangerines from cusco",
            )
            self.assertEqual(hs, "080520")

    def test_resolve_hs_code_for_kiwicha_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="kiwicha organica",
            )
            self.assertEqual(hs, "100890")

    def test_resolve_hs_code_for_chia_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="semillas de chia",
            )
            self.assertEqual(hs, "120799")

    def test_resolve_hs_code_for_camu_camu_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="pulpa de camu camu congelada",
            )
            self.assertEqual(hs, "081190")

    def test_resolve_hs_code_for_artichoke_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="alcachofa fresca",
            )
            self.assertEqual(hs, "070991")

    def test_resolve_hs_code_for_aji_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="ají panca deshidratado",
            )
            self.assertEqual(hs, "090421")

    def test_resolve_hs_code_for_banana_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="banano organico fresco",
            )
            self.assertEqual(hs, "080390")

    def test_resolve_hs_code_for_lime_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="limon sutil fresco",
            )
            self.assertEqual(hs, "080550")


if __name__ == "__main__":
    unittest.main()
