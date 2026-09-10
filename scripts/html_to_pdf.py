"""Render an HTML report to PDF with xhtml2pdf (pure Python; used because pandoc is unavailable).

`make submission` prefers `reports/final_report.pdf` whenever it exists and otherwise falls back
to a `.doc` produced by macOS `textutil`; both are approved formats under the brief's section 8.
Running this script is what puts the PDF in place.

xhtml2pdf is NOT a project dependency and is deliberately kept out of `requirements*.txt` — it plays
no part in the reproducible pipeline. Build in a throwaway environment:

    python -m venv /tmp/pdfenv && /tmp/pdfenv/bin/pip install xhtml2pdf
    /tmp/pdfenv/bin/python scripts/html_to_pdf.py reports/final_report.html reports/final_report.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

from xhtml2pdf import pisa

# Print styling. The report is text and tables (it cites figure paths rather than embedding images),
# so the priorities are a readable type scale, tables that survive a narrow page, and headings that
# do not strand themselves at the foot of a page.
PDF_CSS = """
@page { size: A4; margin: 15mm 14mm; }
body { font-family: Helvetica; font-size: 9.5pt; line-height: 1.4; color: #1d2a3a; }
h1 { font-size: 18pt; color: #1f3a5f; }
h2 { font-size: 13.5pt; color: #1f3a5f; margin-top: 15pt; -pdf-keep-with-next: true; }
h3 { font-size: 11pt; color: #1f3a5f; -pdf-keep-with-next: true; }
h4 { font-size: 9.8pt; -pdf-keep-with-next: true; }
table { font-size: 7pt; border-collapse: collapse; width: 100%; margin: 6pt 0; }
th, td { border: 0.5pt solid #9aa8b8; padding: 2pt 3pt; text-align: left; }
th { background: #eef1f5; font-weight: bold; }
code, pre { font-family: Courier; font-size: 8pt; color: #1d2a3a; }
pre { background: #f4f6f8; padding: 4pt 6pt; }
blockquote { background: #fff7e6; border-left: 3pt solid #e0a800; padding: 4pt 8pt; margin: 6pt 0; }
a { color: #1f3a5f; }
img { max-width: 100%; }
"""


def main(src: str, dst: str, page_break_h2: bool = False) -> None:
    html = Path(src).read_text(encoding="utf-8")
    css = PDF_CSS + ("h2 { page-break-before: always; }" if page_break_h2 else "")
    html = (
        html.replace("</head>", f"<style>{css}</style></head>", 1)
        if "</head>" in html
        else f"<style>{css}</style>{html}"
    )
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "wb") as fh:
        status = pisa.CreatePDF(
            html, dest=fh, path=str(Path(src).resolve().parent), encoding="utf-8"
        )
    if status.err:
        raise SystemExit(f"xhtml2pdf reported {status.err} error(s) rendering {src}")
    print(f"wrote {dst} ({Path(dst).stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not 2 <= len(args) <= 3:
        raise SystemExit(__doc__)
    main(args[0], args[1], page_break_h2=len(args) > 2 and args[2] == "--page-break-h2")
