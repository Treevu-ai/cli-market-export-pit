"""Generate executive dossiers from an existing PIT research run."""

from __future__ import annotations

import os
from typing import Any

from .adapters.pit_context import build_context_bundle
from .runner import ProductBrief, _infer_market_code, run_analysis, set_context_bundle


def agents_dependencies_ready() -> tuple[bool, str | None]:
    if not os.getenv("OPENAI_API_KEY"):
        return False, "OPENAI_API_KEY no esta configurada en el servidor."
    try:
        from agents import Agent  # noqa: F401
    except ImportError:
        return (
            False,
            'Dependencias de agentes no instaladas. Ejecuta: pip install -e ".[agents]"',
        )
    return True, None


def agents_status() -> dict[str, Any]:
    ready, reason = agents_dependencies_ready()
    return {
        "ficha_available": ready,
        "reason": reason,
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
    }


async def generate_dossier_for_run(
    *,
    run_id: str,
    report: dict[str, Any],
    query: str,
    target_market: str,
    segment: str = "exportadores y retail premium",
    stage: str = "concepto",
    market_label: str | None = None,
) -> dict[str, Any]:
    """Run the multi-agent workflow using snapshots from an existing PIT report."""
    ready, reason = agents_dependencies_ready()
    if not ready:
        raise RuntimeError(reason or "Agentes no disponibles")

    bundle = build_context_bundle(run_id=run_id, report=report)
    set_context_bundle(bundle)

    market_name = market_label or _market_label(target_market)
    brief = ProductBrief(
        product=query,
        market=market_name,
        segment=segment,
        stage=stage,
    )
    dossier_markdown = await run_analysis(brief)
    score = report.get("score") or {}
    return {
        "run_id": run_id,
        "dossier_markdown": dossier_markdown,
        "pit_recommendation": score.get("recommendation"),
        "pit_opportunity_score": score.get("opportunity_score"),
        "segment": segment,
        "stage": stage,
    }


def _market_label(target_market: str) -> str:
    code = _infer_market_code(target_market)
    labels = {
        "US": "Estados Unidos",
        "PE": "Peru",
        "MX": "Mexico",
        "CL": "Chile",
        "CO": "Colombia",
        "EU": "Union Europea",
        "ES": "Espana",
    }
    return labels.get(code, code)
