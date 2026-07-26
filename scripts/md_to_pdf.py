"""Convert markdown proposal to a styled PDF via Playwright."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

CSS = """
@page { size: A4; margin: 22mm 18mm; }
body {
  font-family: "Segoe UI", Arial, sans-serif;
  font-size: 11pt;
  line-height: 1.55;
  color: #1a1a1a;
}
h1 { font-size: 20pt; color: #0f3d2e; margin-top: 0; border-bottom: 2px solid #0f3d2e; padding-bottom: 6px; }
h2 { font-size: 14pt; color: #0f3d2e; margin-top: 22px; }
h3 { font-size: 12pt; color: #1f5c45; margin-top: 16px; }
blockquote {
  background: #f4f8f6;
  border-left: 4px solid #2e7d57;
  margin: 14px 0;
  padding: 10px 14px;
  font-size: 10pt;
}
table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 10pt; }
th, td { border: 1px solid #cfd8d3; padding: 7px 9px; vertical-align: top; }
th { background: #e8f3ed; text-align: left; }
tr:nth-child(even) td { background: #fafcfb; }
code, pre { font-family: Consolas, monospace; font-size: 9pt; }
pre { background: #f6f8f7; padding: 10px; border-radius: 4px; white-space: pre-wrap; }
hr { border: none; border-top: 1px solid #d7e2dc; margin: 20px 0; }
strong { color: #123f2f; }
p { margin: 8px 0; }
ul, ol { margin: 8px 0 8px 20px; }
img { max-width: 100%; height: auto; border: 1px solid #d7e2dc; border-radius: 6px; margin: 10px 0; }
footer-note { display: block; margin-top: 28px; font-size: 9pt; color: #555; }
"""


def md_to_html(md_text: str, base_dir: Path) -> str:
    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
    )
    # Resolve relative image paths for Playwright rendering.
    def _replace_image(match: re.Match[str]) -> str:
        src = match.group(1)
        if src.startswith(("http://", "https://", "data:")):
            return match.group(0)
        resolved = (base_dir / src).resolve().as_uri()
        return f'<img src="{resolved}" alt="">'

    html_body = re.sub(r'<img src="([^"]+)"', _replace_image, html_body)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>Propuesta</title>
  <style>{CSS}</style>
</head>
<body>{html_body}</body>
</html>"""


def export_pdf(input_md: Path, output_pdf: Path) -> None:
    md_text = input_md.read_text(encoding="utf-8")
    base_dir = input_md.parent.resolve()
    html = md_to_html(md_text, base_dir)
    html_path = output_pdf.with_suffix(".html").resolve()
    html_path.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.pdf(
            path=str(output_pdf),
            format="A4",
            print_background=True,
            margin={"top": "18mm", "bottom": "18mm", "left": "16mm", "right": "16mm"},
        )
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_md", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.input_md.with_suffix(".pdf")
    export_pdf(args.input_md, output)
    print(output)


if __name__ == "__main__":
    main()
