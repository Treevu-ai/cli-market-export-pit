"""Scoring engine and opportunity calculation."""

from __future__ import annotations

from typing import Any

from .storage import ResearchStore


def estimate_coverage(domain: str, payloads: dict[str, Any]) -> float:
    if not payloads:
        return 0.0
    if domain == "science":
        return 0.9 if payloads.get("openalex_aggregation") else 0.4
    if domain == "patent":
        return 0.9 if payloads.get("epo_ops_aggregation") else 0.0
    if domain == "trend":
        return 0.8 if payloads.get("gdelt_aggregation") else 0.0
    if domain == "trade":
        return 0.9 if payloads.get("comtrade_aggregation") else 0.0
    if domain == "regulatory":
        return 0.7 if payloads.get("regulatory_aggregation") else 0.0
    if domain == "sustainability":
        return 0.7 if payloads.get("climatiq_aggregation") else 0.0
    if domain == "technology_scout":
        return 0.7 if payloads.get("techscout_aggregation") else 0.0
    return 0.0


def estimate_score(domain: str, payloads: dict[str, Any]) -> int:
    if not payloads:
        return 0
    if domain == "science":
        agg = payloads.get("openalex_aggregation", {})
        count = len(agg.get("top_topics", []))
        return min(100, max(0, count * 10))
    if domain == "patent":
        agg = payloads.get("epo_ops_aggregation", {})
        count = agg.get("patents_count", 0)
        return min(100, max(0, count * 5))
    if domain == "trend":
        agg = payloads.get("gdelt_aggregation", {})
        count = agg.get("news_volume", 0)
        return min(100, max(0, count * 5))
    if domain == "trade":
        agg = payloads.get("comtrade_aggregation", {})
        count = agg.get("trade_records_count", 0)
        return min(100, max(0, count * 20))
    if domain == "regulatory":
        agg = payloads.get("regulatory_aggregation", {})
        count = agg.get("total_records", 0)
        return min(100, max(0, count * 15))
    if domain == "sustainability":
        agg = payloads.get("climatiq_aggregation", {})
        count = agg.get("activity_count", 0)
        return min(100, max(0, count * 10))
    if domain == "technology_scout":
        agg = payloads.get("techscout_aggregation", {})
        count = agg.get("total_projects", 0)
        return min(100, max(0, count * 10))
    return 0


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
        dimensions: dict[str, Any] = {}
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
        total_weight = sum(self.weights.values())
        coverage_factor = coverage_weight_sum / total_weight if total_weight else 0.0
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


class ScoringService:
    def __init__(self, store: ResearchStore, engine: ScoringEngine | None = None) -> None:
        self.store = store
        self.engine = engine or ScoringEngine()

    def build_domain_scores(self, run_id: str) -> list[dict[str, Any]]:
        summaries = self.store.get_domain_summaries(run_id)
        domain_scores: list[dict[str, Any]] = []
        for domain, payloads in summaries.items():
            if domain not in self.engine.weights:
                continue
            coverage = estimate_coverage(domain, payloads)
            domain_scores.append({
                "domain": domain,
                "score": estimate_score(domain, payloads),
                "confidence": "high" if coverage > 0.7 else "medium",
                "weight": self.engine.weights.get(domain, 0.0),
                "coverage": coverage,
            })
        return domain_scores

    def calculate_scores(self, run_id: str) -> dict[str, Any]:
        domain_scores = self.build_domain_scores(run_id)
        result = self.engine.calculate(domain_scores)
        result["dimensions"] = list(self.engine.weights.keys())
        claims = self._build_claims(run_id, domain_scores, result)
        for item in domain_scores:
            self.store.save_domain_score(
                research_run_id=run_id,
                domain=item["domain"],
                score=item["score"],
                confidence=item["confidence"],
                weight=item["weight"],
                coverage=item["coverage"],
            )
        self.store.save_opportunity_score(
            research_run_id=run_id,
            score_version=result["score_version"],
            opportunity_score=result["opportunity_score"],
            coverage_factor=result["coverage_factor"],
            recommendation=result["recommendation"],
            alerts=result["alerts"],
            exclusions=result["exclusions"],
            dimensions=domain_scores,
        )
        for claim in claims:
            self.store.save_claim(
                research_run_id=run_id,
                domain=claim["domain"],
                statement=claim["statement"],
                value=claim["value"],
                unit=claim["unit"],
                method=claim["method"],
                period_from=claim["period_from"],
                period_to=claim["period_to"],
                geography=claim["geography"],
                confidence=claim["confidence"],
                limitations=claim["limitations"],
                source_refs=claim["source_refs"],
            )
        result["claims"] = claims
        return result

    def _build_claims(self, run_id: str, domain_scores: list[dict[str, Any]], result: dict[str, Any]) -> list[dict[str, Any]]:
        claims = []
        for item in domain_scores:
            domain = item["domain"]
            claims.append({
                "domain": domain,
                "statement": f"{domain.capitalize()} score estimated from available evidence.",
                "value": item["score"],
                "unit": "index",
                "method": "heuristic_v1",
                "period_from": None,
                "period_to": None,
                "geography": None,
                "confidence": item["confidence"],
                "limitations": "Automated estimation; human review recommended.",
                "source_refs": [run_id],
            })
        claims.append({
            "domain": "opportunity",
            "statement": f"Opportunity score calculated with coverage factor {result['coverage_factor']:.2f}.",
            "value": result["opportunity_score"],
            "unit": "index",
            "method": "weighted_sum_v1",
            "period_from": None,
            "period_to": None,
            "geography": None,
            "confidence": "medium",
            "limitations": "Weights are initial hypothesis; calibration pending.",
            "source_refs": [run_id],
        })
        return claims
