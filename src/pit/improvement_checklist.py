"""Actionable checklist when PIT analysis coverage or connectors are weak."""

from __future__ import annotations

import unicodedata
from typing import Any

DOMAIN_LABELS = {
    "science": "Ciencia",
    "patent": "Patentes",
    "trend": "Tendencias",
    "trade": "Comercio exterior",
    "commerce": "Gondola / CLI Market",
}

CONNECTOR_HINTS: list[dict[str, Any]] = [
    {
        "aggregation": "epo_ops_aggregation",
        "domain": "patent",
        "title": "Patentes (EPO OPS)",
        "action": "Configura EPO_OPS_CONSUMER_KEY y EPO_OPS_CONSUMER_SECRET en .env para enriquecer patentes.",
    },
    {
        "aggregation": "climarket_aggregation",
        "domain": "commerce",
        "title": "Precios en gondola (CLI Market)",
        "action": "Configura CLIMARKET_API_KEY para comparar productos y precios en el mercado destino.",
    },
    {
        "aggregation": "comtrade_aggregation",
        "domain": "trade",
        "title": "Comercio exterior (UN Comtrade)",
        "action": "Usa un producto con codigo HS en taxonomia o indica hs_code manualmente en la consola.",
    },
    {
        "aggregation": "climatiq_aggregation",
        "title": "Sostenibilidad (Climatiq)",
        "action": "Configura CLIMATIQ_API_KEY para huella de carbono del producto.",
    },
    {
        "aggregation": "regulatory_aggregation",
        "title": "Regulacion alimentaria",
        "action": "Verifica mercado destino (US/EU) y que el conector regulatorio haya corrido sin errores.",
    },
]

SOURCE_ALERTS: list[tuple[str, str, str]] = [
    (
        "semanticscholar",
        "429",
        "Semantic Scholar limito la consulta: agrega SEMANTICSCHOLAR_API_KEY al .env y reinicia PIT.",
    ),
    (
        "semanticscholar",
        "failed",
        "Semantic Scholar no respondio: agrega SEMANTICSCHOLAR_API_KEY o reintenta mas tarde.",
    ),
    (
        "climarket",
        "401",
        "CLI Market rechazo la API key: revisa CLIMARKET_API_KEY en .env.",
    ),
    (
        "epo_ops",
        "401",
        "EPO OPS requiere credenciales validas (EPO_OPS_CONSUMER_KEY / SECRET).",
    ),
]


def build_improvement_checklist(
    *,
    summaries: dict[str, Any],
    scores: dict[str, Any],
    domain_scores: list[dict[str, Any]] | None = None,
    sources: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Return prioritized checklist items for the analyze console and PDF."""
    items: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(priority: str, title: str, action: str) -> None:
        key = f"{title}:{action}"
        if key in seen:
            return
        seen.add(key)
        items.append({"priority": priority, "title": title, "action": action})

    coverage_factor = scores.get("coverage_factor")
    if coverage_factor is not None and coverage_factor < 0.6:
        add(
            "high",
            "Cobertura insuficiente",
            "El score global esta penalizado por dominios vacios. Completa las acciones siguientes y vuelve a ejecutar el pipeline.",
        )

    recommendation = scores.get("recommendation")
    if recommendation == "Insufficient evidence":
        add(
            "high",
            "Recomendacion: evidencia insuficiente",
            "No tomes decisiones de exportacion solo con este run; activa conectores faltantes o amplia el limite por fuente.",
        )

    for alert in scores.get("alerts") or []:
        alert_text = str(alert)
        lower = alert_text.lower()
        if "semantic scholar" in lower and "429" in lower:
            add("high", "Semantic Scholar", SOURCE_ALERTS[0][2])
        elif "semantic scholar" in lower:
            add("medium", "Semantic Scholar", SOURCE_ALERTS[1][2])

    if sources:
        for source_row in sources:
            source_name = str(source_row.get("source", "")).lower()
            status = str(source_row.get("status", "")).lower()
            http_status = str(source_row.get("http_status", ""))
            for needle, status_match, message in SOURCE_ALERTS:
                if needle in source_name and (status_match in status or status_match in http_status):
                    add("medium", needle.upper(), message)

    for hint in CONNECTOR_HINTS:
        aggregation = hint["aggregation"]
        if summaries.get(aggregation):
            continue
        domain = hint.get("domain")
        if domain and domain_scores:
            domain_row = next((row for row in domain_scores if row["domain"] == domain), None)
            if domain_row and domain_row.get("coverage", 0) >= 0.5:
                continue
        add("medium", hint["title"], hint["action"])

    if domain_scores:
        for row in domain_scores:
            coverage = row.get("coverage", 0)
            if coverage >= 0.35:
                continue
            label = DOMAIN_LABELS.get(row["domain"], row["domain"])
            add(
                "low",
                f"Dominio debil: {label}",
                f"Cobertura {coverage:.0%} en {label}. Revisa conectores asociados o amplia la consulta.",
            )

    order = {"high": 0, "medium": 1, "low": 2}
    items.sort(key=lambda item: order.get(item["priority"], 9))
    return items[:8]


def pdf_safe_text(text: str) -> str:
    """Strip characters unsupported by core PDF fonts."""
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")
