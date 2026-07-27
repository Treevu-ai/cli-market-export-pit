"""OpenAI Agents SDK runner for CLI Market Product Intelligence."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .adapters.pit_context import PITClient, PITContextBundle
from .instructions import (
    BRIEF_INSTRUCTIONS,
    COMMERCIAL_INSTRUCTIONS,
    DESIGN_INSTRUCTIONS,
    DOSSIER_INSTRUCTIONS,
    MARKET_INSTRUCTIONS,
    ORCHESTRATOR_INSTRUCTIONS,
    RED_TEAM_INSTRUCTIONS,
    REGULATORY_INSTRUCTIONS,
    SCIENTIFIC_INSTRUCTIONS,
)

_context_bundle: PITContextBundle | None = None


class ProductBrief(BaseModel):
    product: str = Field(description="Producto o concepto a evaluar.")
    market: str = Field(description="Mercado local o internacional objetivo.")
    segment: str = Field(description="Segmento de cliente o consumidor.")
    stage: str = Field(description="Etapa: idea, concepto, prototipo, piloto o escalamiento.")
    objective: str = Field(
        default=(
            "Determinar si existe una oportunidad defendible y cómo diseñar "
            "un producto competitivo antes de comprometer inversión relevante."
        )
    )
    constraints: list[str] = Field(default_factory=list)


def set_context_bundle(bundle: PITContextBundle | None) -> None:
    global _context_bundle
    _context_bundle = bundle


def _load_json_file(env_name: str) -> dict[str, Any]:
    path = os.getenv(env_name)
    if not path:
        return {
            "status": "not_configured",
            "message": f"No se configuró {env_name}. No inventar datos.",
        }

    file_path = Path(path)
    if not file_path.exists():
        return {
            "status": "missing",
            "message": f"No existe el archivo indicado en {env_name}: {file_path}",
        }

    try:
        return {
            "status": "ok",
            "path": str(file_path),
            "data": json.loads(file_path.read_text(encoding="utf-8")),
        }
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "error", "message": str(exc)}


def _snapshot_payload(domain: str) -> dict[str, Any]:
    if _context_bundle is not None:
        data = {
            "scientific": _context_bundle.scientific,
            "market": _context_bundle.market,
            "regulatory": _context_bundle.regulatory,
        }[domain]
        return {
            "status": data.get("status", "ok"),
            "source": "pit",
            "run_id": _context_bundle.run_id,
            "data": data,
        }
    env_name = {
        "scientific": "SCIENTIFIC_CONTEXT_FILE",
        "market": "CLI_MARKET_CONTEXT_FILE",
        "regulatory": "REGULATORY_CONTEXT_FILE",
    }[domain]
    return _load_json_file(env_name)


def _require_agents_sdk():
    try:
        from agents import Agent, Runner, function_tool
    except ImportError as exc:
        raise SystemExit(
            "Missing optional dependency openai-agents. Install with: pip install -e \".[agents]\""
        ) from exc
    return Agent, Runner, function_tool


def build_agents():
    Agent, Runner, function_tool = _require_agents_sdk()

    @function_tool
    def load_cli_market_context() -> str:
        """Carga datos de góndola, precios y competencia desde PIT o snapshot JSON."""
        return json.dumps(_snapshot_payload("market"), ensure_ascii=False)

    @function_tool
    def load_scientific_context() -> str:
        """Carga evidencia científica y patentaria desde PIT o snapshot JSON."""
        return json.dumps(_snapshot_payload("scientific"), ensure_ascii=False)

    @function_tool
    def load_regulatory_context() -> str:
        """Carga requisitos regulatorios desde PIT o snapshot JSON."""
        return json.dumps(_snapshot_payload("regulatory"), ensure_ascii=False)

    brief_agent = Agent(name="CLI Brief Architect", instructions=BRIEF_INSTRUCTIONS)
    scientific_agent = Agent(
        name="Scientific Evidence Agent",
        instructions=SCIENTIFIC_INSTRUCTIONS + "\nDebes usar load_scientific_context antes de emitir hallazgos.",
        tools=[load_scientific_context],
    )
    market_agent = Agent(
        name="CLI Market Intelligence Agent",
        instructions=MARKET_INSTRUCTIONS + "\nDebes usar load_cli_market_context antes de emitir cifras o comparaciones.",
        tools=[load_cli_market_context],
    )
    regulatory_agent = Agent(
        name="Regulatory Readiness Agent",
        instructions=REGULATORY_INSTRUCTIONS + "\nDebes usar load_regulatory_context antes de emitir hallazgos.",
        tools=[load_regulatory_context],
    )
    product_design_agent = Agent(name="Competitive Product Designer", instructions=DESIGN_INSTRUCTIONS)
    economics_agent = Agent(name="Commercial Feasibility Agent", instructions=COMMERCIAL_INSTRUCTIONS)
    critic_agent = Agent(name="Red Team Opportunity Critic", instructions=RED_TEAM_INSTRUCTIONS)
    report_agent = Agent(name="Opportunity Dossier Writer", instructions=DOSSIER_INSTRUCTIONS)

    orchestrator_agent = Agent(
        name="CLI Product Intelligence Orchestrator",
        instructions=ORCHESTRATOR_INSTRUCTIONS
        + """

Secuencia obligatoria:
1. build_product_brief
2. scientific_evidence, market_intelligence y regulatory_readiness
3. competitive_product_design
4. commercial_feasibility
5. red_team_review
6. write_opportunity_dossier

No reemplaces a los especialistas con tu propio conocimiento.
No inventes datos para completar vacíos.
""",
        tools=[
            brief_agent.as_tool(
                tool_name="build_product_brief",
                tool_description="Convierte la idea inicial en un brief y define hipótesis críticas.",
            ),
            scientific_agent.as_tool(
                tool_name="scientific_evidence",
                tool_description="Evalúa evidencia científica, tecnológica y patentaria.",
            ),
            market_agent.as_tool(
                tool_name="market_intelligence",
                tool_description="Analiza góndola, competencia, precios, formatos y espacios de mercado.",
            ),
            regulatory_agent.as_tool(
                tool_name="regulatory_readiness",
                tool_description="Evalúa regulación, etiquetado, claims y requisitos del mercado.",
            ),
            product_design_agent.as_tool(
                tool_name="competitive_product_design",
                tool_description="Diseña conceptos de producto basados en la evidencia consolidada.",
            ),
            economics_agent.as_tool(
                tool_name="commercial_feasibility",
                tool_description="Evalúa posicionamiento, canal, margen preliminar y pruebas comerciales.",
            ),
            critic_agent.as_tool(
                tool_name="red_team_review",
                tool_description="Cuestiona la oportunidad y recomienda GO, CONDITIONAL GO, PIVOT o NO-GO.",
            ),
            report_agent.as_tool(
                tool_name="write_opportunity_dossier",
                tool_description="Redacta la Ficha de Oportunidad de Producto para decisión ejecutiva.",
            ),
        ],
    )
    return orchestrator_agent, Runner


async def run_analysis(brief: ProductBrief) -> str:
    orchestrator_agent, Runner = build_agents()
    prompt = f"""
Analiza la siguiente iniciativa:

{brief.model_dump_json(indent=2)}

Usa la secuencia completa de subagentes. No omitas ciencia, mercado,
regulación, diseño, viabilidad comercial, red team ni síntesis final.
"""
    result = await Runner.run(orchestrator_agent, prompt, max_turns=30)
    return result.final_output


def resolve_context_bundle(args: argparse.Namespace, brief: ProductBrief) -> PITContextBundle | None:
    if args.skip_pit:
        return None

    client = PITClient(base_url=args.pit_url)
    if args.pit_run_id:
        return client.context_bundle_for_run(args.pit_run_id)

    if args.use_pit:
        target_market = args.target_market or _infer_market_code(brief.market)
        return client.fetch_context_bundle(
            query=brief.product,
            target_market=target_market,
            application=args.application,
            from_publication_date=args.from_publication_date,
            limit=args.limit,
            hs_code=args.hs_code,
        )
    return None


def _infer_market_code(market: str) -> str:
    normalized = market.strip().upper()
    if len(normalized) == 2 and normalized.isalpha():
        return normalized
    aliases = {
        "PERU": "PE",
        "PERÚ": "PE",
        "ESTADOS UNIDOS": "US",
        "UNITED STATES": "US",
        "USA": "US",
        "MEXICO": "MX",
        "MÉXICO": "MX",
        "CHILE": "CL",
        "COLOMBIA": "CO",
        "ESPAÑA": "ES",
        "SPAIN": "ES",
        "EU": "EU",
    }
    return aliases.get(normalized, "US")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CLI Market Product Intelligence multi-agent workflow")
    parser.add_argument("--product", required=True)
    parser.add_argument("--market", required=True)
    parser.add_argument("--segment", required=True)
    parser.add_argument("--stage", default="concepto")
    parser.add_argument("--objective", default=ProductBrief.model_fields["objective"].default)
    parser.add_argument("--constraint", action="append", default=[], help="Puede repetirse.")
    parser.add_argument("--pit-url", default=os.getenv("PIT_API_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--pit-run-id", help="Reutiliza un research run PIT existente.")
    parser.add_argument("--use-pit", action="store_true", help="Ejecuta POST /v1/research-runs/full antes del análisis.")
    parser.add_argument("--skip-pit", action="store_true", help="Usa solo snapshots JSON por variables de entorno.")
    parser.add_argument("--target-market", help="Código ISO de mercado para PIT (ej. US, PE).")
    parser.add_argument("--application", default="functional foods and beverages")
    parser.add_argument("--from-publication-date", default="2021-01-01")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--hs-code")
    parser.add_argument("--save-context", type=Path, help="Guarda el bundle PIT en JSON para auditoría.")
    parser.add_argument("--output", type=Path, help="Guarda la ficha final en un archivo Markdown.")
    return parser.parse_args(argv)


async def async_main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    brief = ProductBrief(
        product=args.product,
        market=args.market,
        segment=args.segment,
        stage=args.stage,
        objective=args.objective,
        constraints=args.constraint,
    )

    bundle = resolve_context_bundle(args, brief)
    set_context_bundle(bundle)
    if bundle and args.save_context:
        args.save_context.write_text(bundle.to_json(), encoding="utf-8")

    output = await run_analysis(brief)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    print(output)
    return 0


def main(argv: list[str] | None = None) -> None:
    raise SystemExit(asyncio.run(async_main(argv)))


if __name__ == "__main__":
    main()
