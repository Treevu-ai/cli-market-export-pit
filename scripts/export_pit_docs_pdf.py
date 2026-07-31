"""Export PIT technical docs and pitch deck to PDF."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from pit.improvement_checklist import pdf_safe_text

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "docs" / "pdf"


class DocPDF(FPDF):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.doc_title = title
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 18, 18)

    def header(self) -> None:
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, pdf_safe_text(self.doc_title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, pdf_safe_text(f"Pagina {self.page_no()}"), align="C")

    def h1(self, text: str) -> None:
        self.ln(4)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(20, 20, 20)
        self.multi_cell(self.epw, 8, pdf_safe_text(text))
        self.set_x(self.l_margin)
        self.ln(2)

    def h2(self, text: str) -> None:
        if self.get_y() > self.h - 30:
            self.add_page()
        self.ln(3)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(30, 30, 30)
        self.multi_cell(self.epw, 6, pdf_safe_text(text))
        self.set_x(self.l_margin)
        self.ln(1)

    def body(self, text: str) -> None:
        if self.get_y() > self.h - 24:
            self.add_page()
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(self.epw, 5, pdf_safe_text(text))
        self.ln(1)

    def bullet(self, text: str) -> None:
        if self.get_y() > self.h - 20:
            self.add_page()
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(self.epw, 5, pdf_safe_text(f"- {text}"))
        self.set_x(self.l_margin)

    def table(self, headers: list[str], rows: list[list[str]]) -> None:
        col_count = len(headers)
        width = self.epw / col_count
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(235, 235, 235)
        for header in headers:
            self.cell(width, 7, pdf_safe_text(header), border=1, fill=True)
        self.ln()
        self.set_font("Helvetica", "", 8)
        for row in rows:
            if self.get_y() > self.h - 22:
                self.add_page()
            for cell in row:
                self.cell(width, 6, pdf_safe_text(cell[:80]), border=1)
            self.ln()
        self.ln(2)


def build_technical_pdf() -> bytes:
    pdf = DocPDF("PIT - Documentacion tecnica | CLI Market Export Intelligence")
    pdf.add_page()

    pdf.h1("PIT - Referencia de arquitectura")
    pdf.body(
        "Motor de inteligencia exportadora con evidencia trazable. "
        "PIT es la capa de datos y scoring; CLI Market Export Intelligence es el producto comercial."
    )
    pdf.body("Repo: github.com/Treevu-ai/cli-market-export-pit | Scoring v1.0-mvp | jul 2026")

    pdf.h2("Principio de diseno")
    pdf.body(
        "Toda afirmacion del reporte debe rastrearse a un source_request con checksum verificable. "
        "Los conectores opcionales pueden fallar sin abortar el pipeline completo."
    )

    pdf.h2("Arquitectura en capas")
    pdf.body(
        "query + target_market -> ResearchService.run_full_pipeline() -> conectores HTTP -> "
        "ResearchStore (raw + evidence) -> domain_summaries -> ScoringService -> "
        "ReportGenerator (JSON/PDF/checklist) -> API REST + web/analyze.html"
    )
    pdf.body(
        "Capa opcional: agents/product_intelligence -> pit_context.py -> run_analysis() -> dossier markdown"
    )
    pdf.table(
        ["Modulo", "Rol", "Responsabilidad"],
        [
            ["api.py", "FastAPI", "Entry point HTTP + static web/"],
            ["research.py", "ResearchService", "Orquesta conectores y enrichment"],
            ["storage.py", "ResearchStore", "SQLite/PostgreSQL, raw files"],
            ["scoring.py", "ScoringService", "Domain scores + opportunity_score"],
            ["reports.py", "ReportGenerator", "JSON, PDF ejecutivo, checklist"],
            ["taxonomy.py", "Sinonimos + HS", "Resolucion Comtrade"],
            ["connectors/", "14 adaptadores", "OpenAlex, Comtrade, EPO..."],
        ],
    )

    pdf.h2("Modelo de datos (SQLite)")
    pdf.table(
        ["Tabla", "Contenido"],
        [
            ["research_runs", "Run raiz: query, mercado, status, cutoff"],
            ["source_requests", "Peticion HTTP + checksum + raw_object_key"],
            ["evidence_records", "Evidencia normalizada, dedupe_key"],
            ["domain_summaries", "Agregaciones JSON por dominio"],
            ["claims", "Afirmaciones con source_refs"],
            ["domain_scores", "Score 0-100 por dominio + coverage"],
            ["opportunity_scores", "Score global + recommendation"],
            ["reports", "Snapshots JSON/PDF"],
        ],
    )

    pdf.h2("Trazabilidad evidencia -> reporte")
    pdf.table(
        ["Paso", "Artefacto", "Campo clave"],
        [
            ["1", "HTTP request", "source_requests.request_url"],
            ["2", "Raw body", "data/raw/{checksum}.bin SHA-256"],
            ["3", "Normalizacion", "evidence_records + dedupe_key"],
            ["4", "Agregacion", "domain_summaries"],
            ["5", "Claims", "claims.source_refs"],
            ["6", "Reporte", "JSON/PDF con run_id + score_version"],
        ],
    )

    pdf.add_page()
    pdf.h2("API REST v1")
    pdf.body("Base: http://127.0.0.1:8000 | OpenAPI: /docs | Auth opcional: X-API-Key")
    pdf.table(
        ["Metodo", "Ruta", "Descripcion"],
        [
            ["POST", "/v1/research-runs", "Run cientifico (OpenAlex)"],
            ["POST", "/v1/research-runs/full", "Pipeline multi-dominio"],
            ["POST", "/v1/research-runs/{id}/enrich/{domain}", "Enrichment puntual"],
            ["GET", "/v1/research-runs/{id}/report", "Reporte JSON + checklist"],
            ["GET", "/v1/research-runs/{id}/report.pdf", "PDF ejecutivo"],
            ["POST", "/v1/research-runs/{id}/ficha", "Dossier multiagente"],
            ["GET", "/v1/agents/status", "Disponibilidad ficha"],
            ["GET", "/v1/connectors/status", "Stats, freshness, quota"],
        ],
    )

    pdf.h2("Conectores")
    pdf.table(
        ["Fuente", "Dominio", "Output"],
        [
            ["openalex / crossref / pubmed", "science", "Papers, citas"],
            ["epo_ops", "patent", "Familias de patente"],
            ["gdelt", "trend", "Noticias y volumen"],
            ["comtrade", "trade", "Flujos UN por HS"],
            ["climarket", "commerce", "Precios gondola"],
            ["openfda / efsa_eurlex", "regulatory", "Regulacion"],
            ["climatiq", "sustainability", "Huella carbono"],
            ["cordis / nih / nsf", "technology_scout", "Proyectos I+D"],
        ],
    )

    pdf.h2("ScoringEngine v1.0-mvp")
    pdf.body("Pesos: science 25%, trade 25%, commerce 20%, patent 15%, trend 15%")
    pdf.table(
        ["Recomendacion", "Condicion", "Accion"],
        [
            ["Investigate", "score >= 70 y coverage >= 0.6", "Profundizar"],
            ["Validate", "50 <= score < 70", "Confirmar hipotesis"],
            ["Deprioritize", "score < 50", "Baja senal"],
            ["Insufficient evidence", "coverage < 0.6", "Dominios vacios"],
        ],
    )

    pdf.h2("Capa Product Intelligence")
    pdf.bullet("9 agentes LLM: brief, scientific, market, regulatory, design, commercial, red_team, dossier")
    pdf.bullet("Entrada: PITContextBundle desde report JSON via pit_context.py")
    pdf.bullet("Salida: dossier_markdown GO / CONDITIONAL GO / PIVOT / NO-GO")
    pdf.bullet("Requisitos: pip install -e \".[agents]\" + OPENAI_API_KEY")

    pdf.h2("Variables de entorno")
    pdf.table(
        ["Variable", "Uso"],
        [
            ["PIT_DB_PATH", "SQLite (default data/pit.db)"],
            ["PIT_RAW_DIR", "Raw inmutable (data/raw)"],
            ["PIT_API_KEY", "Header X-API-Key"],
            ["SEMANTICSCHOLAR_API_KEY", "Menos 429 en science"],
            ["EPO_OPS_*", "Patentes"],
            ["CLIMARKET_API_KEY", "Dominio commerce"],
            ["OPENAI_API_KEY", "Capa agents / ficha"],
        ],
    )

    pdf.h2("Desarrollo local")
    pdf.body("PYTHONPATH=src python -m uvicorn pit.api:app --reload")
    pdf.body("Consola: /analyze.html | Tests: python -m pytest tests")

    return bytes(pdf.output())


def build_pitch_pdf() -> bytes:
    pdf = DocPDF("PIT - Pitch deck | CLI Market Export Intelligence")

    slides = [
        (
            "PIT - Inteligencia exportadora con evidencia trazable",
            [
                "Decide si exportar con fuentes reales, no con slides de consultor.",
                "14+ fuentes | Score 0-100 | Ficha GO/NO-GO",
                "Treevu-ai | jul 2026",
            ],
        ),
        (
            "El problema",
            [
                "Decision sin evidencia: comites basados en intuicion.",
                "Fuentes dispersas: ciencia, Comtrade, gondola en silos.",
                "Costo de consultoria: semanas antes de un filtro GO/NO-GO.",
                "Riesgo regulatorio: claims sin validar FDA/EUR-Lex.",
            ],
        ),
        (
            "La solucion",
            [
                "PIT: motor de evidencia trazable + score exportador.",
                "Agentes: Ficha de Oportunidad narrativa GO/NO-GO.",
                "Evidencia en horas sobre 14+ fuentes publicas.",
                "Trazabilidad SHA-256 en cada respuesta HTTP.",
            ],
        ),
        (
            "Como funciona",
            [
                "1. Consulta: producto + mercado ISO",
                "2. Research run: ID unico rr_xxx",
                "3. Conectores: OpenAlex, Comtrade, CLI Market, EPO...",
                "4. Score 0-100 + recomendacion + checklist",
                "5. Entregables: PDF ejecutivo + Ficha de Oportunidad",
            ],
        ),
        (
            "Diferenciadores",
            [
                "Trazabilidad SHA-256 vs consultoria sin raw auditable.",
                "Pipeline en minutos vs semanas de desk research.",
                "Gondola LATAM via CLI Market integrado.",
                "Dual output: score tecnico + ficha ejecutiva.",
            ],
        ),
        (
            "Cliente ideal (ICP)",
            [
                "Exportadores agro: mango, palta, cafe, uva, pisco.",
                "MIPYMES alimentos: snacks funcionales, superfoods.",
                "CITE / incubadoras: portafolio de innovacion.",
                "Consultores export: evidencia trazable para clientes.",
            ],
        ),
        (
            "Stack de producto",
            [
                "Capa 1 PIT: API + consola /analyze.html",
                "Capa 2 Agentes: product_intelligence (OpenAI)",
                "Capa 3 CLI Market: precios gondola LATAM",
                "Capa 4 Landing: web/ comercial + leads WhatsApp",
            ],
        ),
        (
            "Estado actual (jul 2026)",
            [
                "Pipeline full multi-dominio",
                "PDF ejecutivo + checklist de mejoras",
                "Boton Generar Ficha en consola",
                "Taxonomia HS 10+ cultivos LATAM",
                "44 tests automatizados pasando",
            ],
        ),
        (
            "Roadmap",
            [
                "Q3 2026: links compartibles ?run=rr_xxx, demo bundles",
                "Q4 2026: batch CSV portafolio, scoring regulatory",
                "2027: cola async, PostgreSQL prod, deploy landing",
            ],
        ),
        (
            "Proximo paso",
            [
                "Piloto 3 meses: 5 fichas con evidencia trazable.",
                "Demo: uvicorn pit.api:app -> /analyze.html -> Generar Ficha",
                "Contacto: WhatsApp +51 902 126 765",
            ],
        ),
    ]

    for idx, (title, bullets) in enumerate(slides, start=1):
        pdf.add_page()
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 6, pdf_safe_text(f"Slide {idx} / {len(slides)}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.h1(title)
        for item in bullets:
            pdf.bullet(item)

    return bytes(pdf.output())


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tech_path = OUTPUT_DIR / "pit-docs-tecnico.pdf"
    pitch_path = OUTPUT_DIR / "pit-pitch-deck.pdf"
    tech_path.write_bytes(build_technical_pdf())
    pitch_path.write_bytes(build_pitch_pdf())
    print(f"Wrote {tech_path}")
    print(f"Wrote {pitch_path}")


if __name__ == "__main__":
    main()
