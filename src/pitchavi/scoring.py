"""Scoring engine and opportunity calculation."""

from __future__ import annotations

from typing import Any


class ScoringEngine:
    score_version = "v1.0-mvp"
    weights = {
        "science": 0.30,
        "patent": 0.20,
        "trend": 0.20,
        "trade": 0.30,
    }
    coverage_threshold = 0.60

    def calculate(self, domain_scores: list[dict[str, Any]]) -> dict[str, Any]:
        weighted_sum = 0.0
        coverage_weight_sum = 0.0
        dimensions = {}
        for item in domain_scores:
            domain = item["domain"]
            score = item["score"]
            coverage = item["coverage"]
            weight = self.weights.get(domain, 0.0)
            weighted_sum += weight * score
            coverage_weight_sum += weight * coverage
            dimensions[domain] = {
                "score": score,
                "confidence": item["confidence"],
                "weight": weight,
                "coverage": coverage,
            }
        coverage_factor = coverage_weight_sum / sum(self.weights.values()) if sum(self.weights.values()) else 0.0
        opportunity_score = weighted_sum * coverage_factor
        if coverage_factor < self.coverage_threshold:
            recommendation = "Insufficient evidence"
        elif opportunity_score >= 70:
            recommendation = "Investigate"
        elif opportunity_score >= 50:
            recommendation = "Validate"
        else:
            recommendation = "Deprioritize"
        return {
            "score_version": self.score_version,
            "opportunity_score": round(opportunity_score, 1),
            "coverage_factor": round(coverage_factor, 2),
            "recommendation": recommendation,
            "dimensions": dimensions,
            "alerts": [],
            "exclusions": [],
        }
