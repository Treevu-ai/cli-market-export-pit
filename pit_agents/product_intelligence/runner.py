"""Anthropic Messages API runner for CLI Market Product Intelligence."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any, Callable

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

MODEL = "claude-opus-5"
# Mirrors the old openai-agents Runner.run(..., max_turns=30) ceiling, applied
# per tool-use loop (each sub-agent's own loop, and the orchestrator's loop).
MAX_TURNS = 30

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


def _require_anthropic_sdk():
    try:
        import anthropic
    except ImportError as exc:
        raise SystemExit(
            "Missing optional dependency anthropic. Install with: pip install -e \".[agents]\""
        ) from exc
    return anthropic


_client_singleton: Any = None


def _client() -> Any:
    """Lazily construct the Anthropic client (reads ANTHROPIC_API_KEY from the env)."""
    global _client_singleton
    if _client_singleton is None:
        anthropic_module = _require_anthropic_sdk()
        _client_singleton = anthropic_module.Anthropic()
    return _client_singleton


def _final_text(response: Any) -> str:
    for block in response.content:
        if block.type == "text":
            return block.text
    return ""


def _run_single_turn_agent(*, instructions: str, prompt: str) -> str:
    response = _client().messages.create(
        model=MODEL,
        max_tokens=8000,
        system=instructions,
        messages=[{"role": "user", "content": prompt}],
    )
    return _final_text(response)


def _run_context_agent(*, instructions: str, prompt: str, tool_name: str, domain: str) -> str:
    """Mirrors the old single-tool sub-agent pattern: the model must call its
    one context-loading tool before answering, so this runs a small tool-use
    loop instead of a single call."""
    tool_def = {
        "name": tool_name,
        "description": f"Carga el contexto de {domain} desde PIT o snapshot JSON.",
        "input_schema": {"type": "object", "properties": {}},
    }
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
    response = _client().messages.create(
        model=MODEL, max_tokens=8000, system=instructions, tools=[tool_def], messages=messages,
    )
    turns = 0
    while response.stop_reason == "tool_use" and turns < MAX_TURNS:
        turns += 1
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use" and block.name == tool_name:
                result = json.dumps(_snapshot_payload(domain), ensure_ascii=False)
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
        messages.append({"role": "user", "content": tool_results})
        response = _client().messages.create(
            model=MODEL, max_tokens=8000, system=instructions, tools=[tool_def], messages=messages,
        )
    if response.stop_reason == "tool_use":
        raise RuntimeError(f"Sub-agent '{tool_name}' exceeded max turns ({MAX_TURNS}) without finishing")
    return _final_text(response)


def _run_brief_agent(task: str) -> str:
    return _run_single_turn_agent(instructions=BRIEF_INSTRUCTIONS, prompt=task)


def _run_scientific_agent(task: str) -> str:
    return _run_context_agent(
        instructions=SCIENTIFIC_INSTRUCTIONS + "\nDebes usar load_scientific_context antes de emitir hallazgos.",
        prompt=task,
        tool_name="load_scientific_context",
        domain="scientific",
    )


def _run_market_agent(task: str) -> str:
    return _run_context_agent(
        instructions=MARKET_INSTRUCTIONS + "\nDebes usar load_cli_market_context antes de emitir cifras o comparaciones.",
        prompt=task,
        tool_name="load_cli_market_context",
        domain="market",
    )


def _run_regulatory_agent(task: str) -> str:
    return _run_context_agent(
        instructions=REGULATORY_INSTRUCTIONS + "\nDebes usar load_regulatory_context antes de emitir hallazgos.",
        prompt=task,
        tool_name="load_regulatory_context",
        domain="regulatory",
    )


def _run_product_design_agent(task: str) -> str:
    return _run_single_turn_agent(instructions=DESIGN_INSTRUCTIONS, prompt=task)


def _run_commercial_agent(task: str) -> str:
    return _run_single_turn_agent(instructions=COMMERCIAL_INSTRUCTIONS, prompt=task)


def _run_red_team_agent(task: str) -> str:
    return _run_single_turn_agent(instructions=RED_TEAM_INSTRUCTIONS, prompt=task)


def _run_dossier_agent(task: str) -> str:
    return _run_single_turn_agent(instructions=DOSSIER_INSTRUCTIONS, prompt=task)


_DELEGATE_TOOL_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "task": {
            "type": "string",
            "description": "Instrucción detallada para el especialista, con todo el contexto necesario.",
        }
    },
    "required": ["task"],
}

_DELEGATE_TOOLS: list[dict[str, Any]] = [
    {
        "name": "build_product_brief",
        "description": "Convierte la idea inicial en un brief y define hipótesis críticas.",
        "input_schema": _DELEGATE_TOOL_INPUT_SCHEMA,
    },
    {
        "name": "scientific_evidence",
        "description": "Evalúa evidencia científica, tecnológica y patentaria.",
        "input_schema": _DELEGATE_TOOL_INPUT_SCHEMA,
    },
    {
        "name": "market_intelligence",
        "description": "Analiza góndola, competencia, precios, formatos y espacios de mercado.",
        "input_schema": _DELEGATE_TOOL_INPUT_SCHEMA,
    },
    {
        "name": "regulatory_readiness",
        "description": "Evalúa regulación, etiquetado, claims y requisitos del mercado.",
        "input_schema": _DELEGATE_TOOL_INPUT_SCHEMA,
    },
    {
        "name": "competitive_product_design",
        "description": "Diseña conceptos de producto basados en la evidencia consolidada.",
        "input_schema": _DELEGATE_TOOL_INPUT_SCHEMA,
    },
    {
        "name": "commercial_feasibility",
        "description": "Evalúa posicionamiento, canal, margen preliminar y pruebas comerciales.",
        "input_schema": _DELEGATE_TOOL_INPUT_SCHEMA,
    },
    {
        "name": "red_team_review",
        "description": "Cuestiona la oportunidad y recomienda GO, CONDITIONAL GO, PIVOT o NO-GO.",
        "input_schema": _DELEGATE_TOOL_INPUT_SCHEMA,
    },
    {
        "name": "write_opportunity_dossier",
        "description": "Redacta la Ficha de Oportunidad de Producto para decisión ejecutiva.",
        "input_schema": _DELEGATE_TOOL_INPUT_SCHEMA,
    },
]

_DELEGATE_HANDLERS: dict[str, Callable[[str], str]] = {
    "build_product_brief": _run_brief_agent,
    "scientific_evidence": _run_scientific_agent,
    "market_intelligence": _run_market_agent,
    "regulatory_readiness": _run_regulatory_agent,
    "competitive_product_design": _run_product_design_agent,
    "commercial_feasibility": _run_commercial_agent,
    "red_team_review": _run_red_team_agent,
    "write_opportunity_dossier": _run_dossier_agent,
}

_ORCHESTRATOR_SEQUENCE = """

Secuencia obligatoria:
1. build_product_brief
2. scientific_evidence, market_intelligence y regulatory_readiness
3. competitive_product_design
4. commercial_feasibility
5. red_team_review
6. write_opportunity_dossier

No reemplaces a los especialistas con tu propio conocimiento.
No inventes datos para completar vacíos.
"""


def _run_orchestrator(prompt: str) -> str:
    """Agents-as-tools orchestration: each delegate tool call runs a nested
    Messages API call (via _DELEGATE_HANDLERS) and its text result is returned
    as the tool_result, mirroring the old Agent.as_tool() pattern."""
    system = ORCHESTRATOR_INSTRUCTIONS + _ORCHESTRATOR_SEQUENCE
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
    response = _client().messages.create(
        model=MODEL, max_tokens=16000, system=system, tools=_DELEGATE_TOOLS, messages=messages,
    )
    turns = 0
    while response.stop_reason == "tool_use" and turns < MAX_TURNS:
        turns += 1
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            handler = _DELEGATE_HANDLERS.get(block.name)
            if handler is None:
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Unknown tool: {block.name}",
                        "is_error": True,
                    }
                )
                continue
            task = block.input.get("task", "") if isinstance(block.input, dict) else ""
            result_text = handler(task)
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result_text})
        messages.append({"role": "user", "content": tool_results})
        response = _client().messages.create(
            model=MODEL, max_tokens=16000, system=system, tools=_DELEGATE_TOOLS, messages=messages,
        )
    if response.stop_reason == "tool_use":
        raise RuntimeError(f"Orchestrator exceeded max turns ({MAX_TURNS}) without finishing")
    return _final_text(response)


async def run_analysis(brief: ProductBrief) -> str:
    prompt = f"""
Analiza la siguiente iniciativa:

{brief.model_dump_json(indent=2)}

Usa la secuencia completa de subagentes. No omitas ciencia, mercado,
regulación, diseño, viabilidad comercial, red team ni síntesis final.
"""
    return await asyncio.to_thread(_run_orchestrator, prompt)


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
