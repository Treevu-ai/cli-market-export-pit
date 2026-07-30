from __future__ import annotations

import unittest

from pit.scoring import ScoringEngine


class ScoringCalibrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = ScoringEngine()

    def _score(self, values: list[tuple[str, int, float]]) -> dict:
        domain_scores = [
            {
                "domain": domain,
                "score": score,
                "coverage": coverage,
                "confidence": "high" if coverage > 0.7 else "medium",
            }
            for domain, score, coverage in values
        ]
        return self.engine.calculate(domain_scores)

    def test_cocoa_flavanol_investigate(self) -> None:
        # All 9 domains present -- weights were rebalanced to fold in
        # regulatory/macro/sustainability/technology_scout, which are now
        # attempted on every real pipeline run alongside the original 5.
        result = self._score([
            ("science", 95, 0.95),
            ("patent", 90, 0.9),
            ("trend", 85, 0.85),
            ("trade", 90, 0.9),
            ("commerce", 85, 0.9),
            ("regulatory", 70, 0.8),
            ("macro", 60, 0.7),
            ("sustainability", 60, 0.75),
            ("technology_scout", 60, 0.75),
        ])
        self.assertEqual(result["recommendation"], "Investigate")
        self.assertGreaterEqual(result["opportunity_score"], 70)

    def test_quinoa_partial_deprioritize(self) -> None:
        result = self._score([
            ("science", 40, 0.9),
            ("patent", 20, 0.9),
            ("trend", 0, 0.0),
            ("trade", 30, 0.9),
        ])
        self.assertIn(result["recommendation"], {"Deprioritize", "Insufficient evidence"})

    def test_novel_ingredient_science_only_insufficient(self) -> None:
        result = self._score([("science", 90, 0.9)])
        self.assertEqual(result["recommendation"], "Insufficient evidence")

    def test_previously_unweighted_domains_now_carry_real_weight(self) -> None:
        """Regression: macro/regulatory/sustainability/technology_scout used
        to be collected as real evidence but silently dropped by
        build_domain_scores (`if domain not in self.engine.weights: continue`)
        -- confirmed live via a full pipeline run where all 4 had real
        summaries but zero rows ever appeared in domain_scores."""
        for domain in ("macro", "regulatory", "sustainability", "technology_scout"):
            self.assertGreater(self.engine.weights.get(domain, 0.0), 0.0)
        self.assertAlmostEqual(sum(self.engine.weights.values()), 1.0)


if __name__ == "__main__":
    unittest.main()
