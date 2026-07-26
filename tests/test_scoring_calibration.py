from __future__ import annotations

import unittest

from pitchavi.scoring import ScoringEngine


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
        result = self._score([
            ("science", 90, 0.9),
            ("patent", 80, 0.9),
            ("trend", 70, 0.8),
            ("trade", 80, 0.9),
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


if __name__ == "__main__":
    unittest.main()
