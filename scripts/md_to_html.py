"""Render `reports/final_report.md` to the self-contained HTML export packaged for submission.

The HTML export previously had no generator in the repository, so editing the Markdown silently left
`reports/final_report.html` (and anything derived from it) stale. This script closes that gap and
reproduces the existing export byte-for-byte: python-markdown with the `extra`, `tables`, `toc` and
`sane_lists` extensions, and the export's original CSS.

`markdown` is already a declared dev dependency (`requirements-dev.txt`), so no extra environment is
needed:

    .venv/bin/python scripts/md_to_html.py reports/final_report.md reports/final_report.html

Regenerate the PDF afterwards with `scripts/html_to_pdf.py` — `make submission` prefers the PDF.
"""

from __future__ import annotations

import sys
from pathlib import Path

import markdown

CSS = (
    "body{font-family:Georgia,serif;max-width:960px;margin:2em auto;line-height:1.45;"
    "color:#222;padding:0 1em} table{border-collapse:collapse;font-size:0.85em;margin:1em 0} "
    "th,td{border:1px solid #bbb;padding:4px 8px} th{background:#f2f2f2} "
    "blockquote{border-left:4px solid #c44e52;background:#fbf3f3;padding:0.5em 1em;margin:1em 0} "
    "code{background:#f4f4f4;padding:1px 4px;border-radius:3px;font-size:0.9em} "
    "h1,h2,h3{color:#1f3a5f} img{max-width:100%}"
)
EXTENSIONS = ["extra", "tables", "toc", "sane_lists"]
# The export carries a short hand-set title rather than the long H1. Kept verbatim so regenerating
# reproduces the committed file exactly; pass a third argument to override it.
TITLE = "Final Report - Student Success Navigator"
FOOTER = (
    "<hr><p><small>Exported from reports/final_report.md by scripts/md_to_html.py "
    "(python-markdown). PDF export: scripts/html_to_pdf.py.</small></p>"
)


def main(src: str, dst: str, title: str = TITLE) -> None:
    body = markdown.markdown(
        Path(src).read_text(encoding="utf-8"), extensions=EXTENSIONS, output_format="html"
    )
    doc = (
        f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title>"
        f"<style>{CSS}</style></head><body>{body}{FOOTER}</body></html>"
    )
    Path(dst).write_text(doc, encoding="utf-8")
    print(f"wrote {dst} ({Path(dst).stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    if not 3 <= len(sys.argv) <= 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
