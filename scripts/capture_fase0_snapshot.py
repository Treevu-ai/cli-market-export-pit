"""Render a Fase 0 research-run snapshot and save a PNG for proposals."""

from __future__ import annotations

import argparse
import html
import json
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from pitchavi.storage import ResearchStore

CSS = """
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 24px;
  font-family: "Segoe UI", Arial, sans-serif;
  background: #eef3f0;
  color: #1a1a1a;
}
.card {
  max-width: 920px;
  margin: 0 auto;
  background: #fff;
  border: 1px solid #d7e2dc;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(15, 61, 46, 0.08);
}
.header {
  background: linear-gradient(135deg, #0f3d2e 0%, #1f5c45 100%);
  color: #fff;
  padding: 18px 22px;
}
.header h1 {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 600;
}
.header p {
  margin: 0;
  font-size: 12px;
  opacity: 0.9;
}
.meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 18px;
  padding: 16px 22px;
  background: #f7faf8;
  border-bottom: 1px solid #e3ebe6;
  font-size: 12px;
}
.meta div strong {
  display: block;
  color: #0f3d2e;
  margin-bottom: 2px;
}
.status {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  background: #d9f0e4;
  color: #0f3d2e;
  font-weight: 600;
  font-size: 11px;
}
.section {
  padding: 16px 22px 20px;
}
.section h2 {
  margin: 0 0 10px;
  font-size: 14px;
  color: #0f3d2e;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}
th, td {
  border: 1px solid #d7e2dc;
  padding: 8px 9px;
  vertical-align: top;
}
th {
  background: #e8f3ed;
  text-align: left;
  color: #123f2f;
}
tr:nth-child(even) td { background: #fafcfb; }
.badge {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 4px;
  background: #edf5f0;
  color: #1f5c45;
  font-size: 10px;
  font-weight: 600;
}
.footer {
  padding: 10px 22px 14px;
  border-top: 1px solid #e3ebe6;
  font-size: 10px;
  color: #5a6b63;
}
"""


def _sources_label(source_links: list[dict]) -> str:
    sources = sorted({link["source"] for link in source_links})
    labels = {"openalex": "OpenAlex", "crossref": "Crossref"}
    return " + ".join(labels.get(source, source.title()) for source in sources) or "OpenAlex"


def render_html(run: dict) -> str:
    evidence = run["evidence"][:5]
    rows = []
    for index, item in enumerate(evidence, start=1):
        payload = item.get("normalized_payload", {})
        year = (item.get("published_at") or payload.get("publication_date") or "—")[:4]
        citations = payload.get("cited_by_count", "—")
        rows.append(
            f"""
            <tr>
              <td>{index}</td>
              <td>{html.escape(item['title'])}</td>
              <td>{html.escape(str(year))}</td>
              <td>{html.escape(str(citations))}</td>
              <td><span class="badge">{html.escape(_sources_label(item.get('source_links', [])))}</span></td>
            </tr>
            """
        )

    created = run.get("created_at", "")[:10]
    run_short = run["id"][:11] + "…"
    status_label = "Completada" if run["status"] == "completed" else run["status"]

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>Pitchavi — consulta Fase 0</title>
  <style>{CSS}</style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h1>Pitchavi · Consulta de investigación</h1>
      <p>Fase 0 — evidencia científica trazable · julio 2026</p>
    </div>
    <div class="meta">
      <div><strong>Producto consultado</strong>Arándano congelado y antocianinas</div>
      <div><strong>Mercado destino</strong>Estados Unidos (US)</div>
      <div><strong>Aplicación</strong>Exportación e ingredientes funcionales</div>
      <div><strong>Periodo</strong>Publicaciones desde 2021</div>
      <div><strong>Consulta registrada</strong>{html.escape(run_short)}</div>
      <div><strong>Estado</strong><span class="status">{html.escape(status_label)}</span></div>
    </div>
    <div class="section">
      <h2>Hallazgos científicos identificados ({len(run['evidence'])} en total · muestra de 5)</h2>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Publicación</th>
            <th>Año</th>
            <th>Citas</th>
            <th>Fuente respaldada</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    <div class="footer">
      Captura real generada el {html.escape(created)} · cada hallazgo conserva su fuente original consultada
    </div>
  </div>
</body>
</html>"""


def capture(run_id: str, output_png: Path, database_path: Path, raw_directory: Path) -> None:
    store = ResearchStore(database_path, raw_directory)
    run = store.get_run_detail(run_id)
    html_content = render_html(run)
    html_path = output_png.with_suffix(".html")
    html_path.write_text(html_content, encoding="utf-8")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 980, "height": 720})
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        page.locator(".card").screenshot(path=str(output_png))
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--db", type=Path, default=Path("data/pitchavi.db"))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    capture(args.run_id, args.output, args.db, args.raw_dir)
    print(args.output)


if __name__ == "__main__":
    main()
