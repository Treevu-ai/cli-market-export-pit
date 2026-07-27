"""Report generators for JSON and PDF exports."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .improvement_checklist import build_improvement_checklist, pdf_safe_text

RECOMMENDATION_LABELS = {
    "Investigate": "Investigar",
    "Validate": "Validar",
    "Deprioritize": "Depriorizar",
    "Insufficient evidence": "Evidencia insuficiente",
}

COMPLEMENTARY_SUMMARY_KEYS = {
    "regulatory_aggregation": "Regulacion",
    "climatiq_aggregation": "Sostenibilidad",
    "techscout_aggregation": "I+D / proyectos",
}


def _complementary_line(key: str, payload: dict[str, Any]) -> str:
    if key == "regulatory_aggregation":
        total = payload.get("total_records")
        return f"Regulacion: {total} registros" if total is not None else "Regulacion: sin datos"
    if key == "climatiq_aggregation":
        count = payload.get("activity_count")
        return f"Sostenibilidad: {count} actividades" if count is not None else "Sostenibilidad: sin datos"
    if key == "techscout_aggregation":
        total = payload.get("total_projects")
        return f"I+D: {total} proyectos" if total is not None else "I+D: sin datos"
    return key


class ReportGenerator:
    def generate_json(
        self,
        run: dict[str, Any],
        scores: dict[str, Any],
        domain_scores: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        summaries = run.get("summaries", {})
        dimension_map = {
            item["domain"]: {
                "score": item["score"],
                "confidence": item["confidence"],
                "weight": item["weight"],
                "coverage": item["coverage"],
            }
            for item in (domain_scores or [])
        }
        checklist = build_improvement_checklist(
            summaries=summaries,
            scores={**scores, "dimensions": dimension_map},
            domain_scores=domain_scores,
            sources=run.get("sources"),
        )
        return {
            "run_id": run["id"],
            "query": run["query_original"],
            "target_market": run["target_market"],
            "application": run["application"],
            "cutoff_at": run["cutoff_at"],
            "score": {
                "score_version": scores["score_version"],
                "opportunity_score": scores["opportunity_score"],
                "coverage_factor": scores["coverage_factor"],
                "recommendation": scores["recommendation"],
                "dimensions": dimension_map,
                "alerts": scores["alerts"],
                "exclusions": scores["exclusions"],
            },
            "improvement_checklist": checklist,
            "evidence_summary": summaries,
            "claims": scores.get("claims", []),
            "sources": [
                {
                    "source": s["source"],
                    "request_url": s["request_url"],
                    "checksum": s["checksum"],
                    "status": s["status"],
                }
                for s in run.get("sources", [])
            ],
        }

    def generate_pdf(
        self,
        run: dict[str, Any],
        scores: dict[str, Any],
        domain_scores: list[dict[str, Any]] | None = None,
    ) -> bytes:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos

        summaries = run.get("summaries", {})
        dimension_map = {
            item["domain"]: item for item in (domain_scores or [])
        }
        checklist = build_improvement_checklist(
            summaries=summaries,
            scores={**scores, "dimensions": dimension_map},
            domain_scores=domain_scores,
            sources=run.get("sources"),
        )

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=14)
        pdf.add_page()
        pdf.set_margins(14, 14, 14)

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(10, 107, 47)
        pdf.cell(0, 6, pdf_safe_text("CLI Market Export Intelligence"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 9, pdf_safe_text("Resumen ejecutivo exportador (PIT)"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 5, pdf_safe_text(f"Producto: {run['query_original']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(
            0,
            5,
            pdf_safe_text(f"Mercado destino: {run['target_market']}  |  Aplicacion: {run.get('application', '-')}") ,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        pdf.cell(0, 5, pdf_safe_text(f"Generado: {generated}  |  Run: {run['id']}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

        recommendation = RECOMMENDATION_LABELS.get(
            scores["recommendation"],
            scores["recommendation"],
        )
        pdf.set_fill_color(233, 253, 237)
        pdf.set_font("Helvetica", "B", 22)
        pdf.cell(60, 14, pdf_safe_text(f"{scores['opportunity_score']}"), border=1, align="C", fill=True)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 14, pdf_safe_text(f"  {recommendation}"), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(
            0,
            6,
            pdf_safe_text(f"Cobertura global: {scores['coverage_factor']:.0%}  |  Version scoring: {scores['score_version']}"),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.ln(4)

        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, pdf_safe_text("Dominios en el score"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(42, 6, "Dominio", border=1)
        pdf.cell(22, 6, "Score", border=1, align="C")
        pdf.cell(22, 6, "Cobert.", border=1, align="C")
        pdf.cell(22, 6, "Peso", border=1, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 9)
        for domain, row in dimension_map.items():
            pdf.cell(42, 6, pdf_safe_text(domain), border=1)
            pdf.cell(22, 6, str(row.get("score", 0)), border=1, align="C")
            pdf.cell(22, 6, pdf_safe_text(f"{row.get('coverage', 0):.0%}"), border=1, align="C")
            pdf.cell(22, 6, pdf_safe_text(f"{row.get('weight', 0):.0%}"), border=1, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        complementary = [
            _complementary_line(key, summaries[key])
            for key in COMPLEMENTARY_SUMMARY_KEYS
            if key in summaries
        ]
        if complementary:
            pdf.ln(3)
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, pdf_safe_text("Evidencia complementaria"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 9)
            for line in complementary[:3]:
                pdf.multi_cell(pdf.epw, 5, pdf_safe_text(f"- {line}"))

        claims = scores.get("claims") or []
        opportunity_claims = [claim for claim in claims if claim.get("domain") != "opportunity"][:3]
        if opportunity_claims:
            pdf.ln(2)
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, pdf_safe_text("Hallazgos clave"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 9)
            for claim in opportunity_claims:
                pdf.multi_cell(
                    pdf.epw,
                    5,
                    pdf_safe_text(f"- [{claim.get('domain', '-')}] score {claim.get('value', '-')}"),
                )

        if checklist:
            pdf.ln(2)
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, pdf_safe_text("Mejoras sugeridas"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 9)
            for item in checklist[:5]:
                pdf.multi_cell(
                    pdf.epw,
                    5,
                    pdf_safe_text(f"- [{item['priority'].upper()}] {item['title']}: {item['action']}"),
                )

        pdf.ln(4)
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(90, 90, 90)
        pdf.multi_cell(
            pdf.epw,
            4,
            pdf_safe_text(
                "Evidencia trazable SHA-256. Este resumen no sustituye asesoria legal ni regulatoria. "
                "Revise fuentes en el reporte JSON completo."
            ),
        )
        return bytes(pdf.output())
