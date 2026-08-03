from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pit.storage import ResearchStore
from pit.taxonomy import (
    TAXONOMY_NAME,
    TAXONOMY_VERSION,
    ensure_default_taxonomy,
    expand_query_with_synonyms,
    resolve_hs_code,
)


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

    def test_resolve_hs_code_for_paprika_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="paprika molida para exportacion",
            )
            self.assertEqual(hs, "090422")

    def test_resolve_hs_code_for_goldenberry_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="aguaymanto deshidratado para exportacion",
            )
            self.assertEqual(hs, "081090")

    def test_resolve_hs_code_for_turmeric_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="curcuma en polvo organico",
            )
            self.assertEqual(hs, "091030")

    def test_resolve_hs_code_for_fig_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="higos frescos para exportacion",
            )
            self.assertEqual(hs, "080420")

    def test_resolve_hs_code_for_passion_fruit_synonym(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            hs = resolve_hs_code(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="pulpa de maracuya congelada",
            )
            self.assertEqual(hs, "200899")


    def test_expand_query_with_synonyms_appends_goldenberry_for_aguaymanto(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            expanded = expand_query_with_synonyms(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="aguaymanto organico",
            )
            self.assertEqual(expanded, "goldenberry organico")

    def test_expand_query_with_synonyms_replaces_instead_of_appending(self) -> None:
        """Regression: appending the synonym alongside the original term
        (e.g. "aguaymanto organico" -> "aguaymanto organico goldenberry")
        made AND-semantics search engines (EPO, CORDIS, ...) require both
        the Spanish and English term simultaneously -- an near-impossible
        match. Confirmed live: this dropped the science score from 100 to
        30 and left patent/commerce/sustainability/techscout at 0. The
        original term must not survive in the expanded query."""
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            ensure_default_taxonomy(store)
            expanded = expand_query_with_synonyms(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="aguaymanto organico",
            )
            self.assertNotIn("aguaymanto", expanded)

    def test_ensure_default_taxonomy_backfills_synonyms_added_after_first_seed(self) -> None:
        """Regression: ensure_default_taxonomy skipped seeding entirely once
        the taxonomy row already existed, so a _SEED_SYNONYMS entry added to
        source after a taxonomy row was first created (e.g. "aguaymanto" ->
        "goldenberry", added 2026-07-28) never reached a pre-existing
        production DB -- confirmed live, "aguaymanto organico" returned zero
        patents/commerce/sustainability/techscout results because the
        synonym was only in code, never in the DB the server actually reads
        from. Simulate a stale DB by creating the taxonomy row directly
        (bypassing the seed loop), then confirm a second
        ensure_default_taxonomy call backfills the missing synonym."""
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            store.create_taxonomy(name=TAXONOMY_NAME, version=TAXONOMY_VERSION)

            taxonomy = store.get_taxonomy(TAXONOMY_NAME, TAXONOMY_VERSION)
            assert taxonomy is not None
            self.assertEqual(store.get_synonyms(taxonomy["id"]), [])

            ensure_default_taxonomy(store)

            expanded = expand_query_with_synonyms(
                store,
                taxonomy_version="cacao-functional-v1",
                query_normalized="aguaymanto organico",
            )
            self.assertIn("goldenberry", expanded)

    def test_ensure_default_taxonomy_does_not_duplicate_rows_on_repeat_calls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ResearchStore(Path(directory) / "pit.db", Path(directory) / "raw")
            taxonomy_id = ensure_default_taxonomy(store)
            first_count = len(store.get_synonyms(taxonomy_id))

            ensure_default_taxonomy(store)
            ensure_default_taxonomy(store)

            self.assertEqual(len(store.get_synonyms(taxonomy_id)), first_count)


if __name__ == "__main__":
    unittest.main()
