"""Render `reports/decks/demo.gif`: a rendered transcript of the Student Success Navigator (T091).

The app is driven **in process** — `ssn.app.app.route()` returns the same Dash component tree the
browser renders, so each frame carries the app's real text, real scores, and real fairness numbers.
The component tree is walked for its text and drawn with Pillow. No browser, no screen recorder, and
no screen-recording permission is involved.

Eight frames cover exactly what T091 asks for: the six adviser pages, the acknowledgement modal, and
the version-mismatch blocking page. Every frame's text is checked against the outcome-label
vocabulary before the GIF is written — the privacy claim is asserted, not eyeballed.

Pillow is already a project dependency (matplotlib). Run:

    .venv/bin/python scripts/render_demo_gif.py [OUT.gif]
"""

from __future__ import annotations

import re
import sys
import textwrap
from dataclasses import replace
from pathlib import Path

from dash.development.base_component import Component
from PIL import Image, ImageDraw, ImageFont

from ssn.app.app import blocked_layout, route
from ssn.app.components import ack_modal
from ssn.app.components.disclaimer import banner
from ssn.app.state import load_state
from ssn.config import load

W, H, PAD, LH, HEAD_H = 1200, 700, 26, 20, 46
PAPER = (250, 251, 252)
INK = (29, 42, 58)
NAVY = (31, 58, 95)
MUTED = (91, 107, 123)
STRIP = (238, 241, 245)
AMBER = (183, 121, 31)
WHITE = (255, 255, 255)

# Target-class values and the label column. None of these may appear on a RECORD-BEARING surface:
# advisers see a support-priority score, never whether a student did or did not complete.
#
# The Model Card is the one documented exception. It is documentation *about* the model and states
# the target encoding ("is_dropout = 1 where source Target = Dropout; Enrolled, Graduate = 0"),
# which describes how the model was trained rather than any student's outcome. It carries no
# per-record data at all, so it is exempt and the exemption is reported when the GIF is built.
OUTCOME_TOKENS = (r"\bis_dropout\b", r"\bDropout\b", r"\bGraduate\b", r"\bEnrolled\b")


def font(size: int = 14):
    for candidate in (
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def walk(node, out: list[str]) -> None:
    """Collect the visible text of a Dash component tree, keeping table rows on one line."""
    if node is None or isinstance(node, bool):
        return
    if isinstance(node, (str, int, float)):
        text = str(node).strip()
        if text:
            out.append(text)
        return
    if isinstance(node, (list, tuple)):
        for child in node:
            walk(child, out)
        return
    if not isinstance(node, Component):
        return

    name = type(node).__name__
    if name == "Tr":  # keep a table row readable as a single line
        cells: list[str] = []
        walk(getattr(node, "children", None), cells)
        if cells:
            out.append("  ".join(cells))
        return
    for option in getattr(node, "options", None) or []:
        if isinstance(option, dict) and option.get("label"):
            out.append(f"[ ] {option['label']}")
    figure = getattr(node, "figure", None)
    if figure is not None:
        title = figure.get("layout", {}).get("title", {}) if isinstance(figure, dict) else None
        title = title.get("text") if isinstance(title, dict) else title
        out.append(f"[chart] {title or 'figure'}")
    placeholder = getattr(node, "placeholder", None)
    if placeholder:
        out.append(f"[input] {placeholder}")
    walk(getattr(node, "children", None), out)


def body_lines(node, skip: set[str], limit: int) -> list[str]:
    raw: list[str] = []
    walk(node, raw)
    lines: list[str] = []
    for item in raw:
        if item in skip or item.startswith("Capacity (") or item == "Advisory only.":
            continue
        for block in item.splitlines():
            block = block.strip()
            if not block:
                continue
            lines.extend(textwrap.wrap(block, width=112) or [""])
        if len(lines) > limit:
            return lines[:limit] + ["…"]
    return lines


def frame(step: str, title: str, lines: list[str], disclaimer: str) -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, HEAD_H], fill=NAVY)
    d.text((PAD, 13), f"{step} · {title}", fill=WHITE, font=font(16))
    y = HEAD_H + 18
    f = font(13)
    for line in lines:
        if y > H - LH - 6:
            d.text((PAD, y), "…", fill=MUTED, font=f)
            break
        colour = AMBER if line.startswith("[ ]") else INK
        d.text((PAD, y), line, fill=colour, font=f)
        y += LH
    # caption strip carrying the standing disclaimer
    cap = textwrap.wrap(disclaimer, width=136)
    strip_h = 14 + LH * len(cap)
    out = Image.new("RGB", (W, H + strip_h), STRIP)
    out.paste(img, (0, 0))
    d2 = ImageDraw.Draw(out)
    yy = H + 7
    for line in cap:
        d2.text((PAD, yy), line, fill=MUTED, font=font(12))
        yy += LH
    return out


def main(out: str = "reports/decks/demo.gif") -> int:
    cfg = load("configs/base.yaml", set_seeds=False)
    state = load_state(cfg)
    skip: list[str] = []
    walk(banner(state), skip)
    skip_set = set(skip)

    record = str(state.ranked.iloc[0]["record_id"])
    blocked = replace(
        state,
        blocked_reason=(
            "Model version mismatch: manifest reports 1.0.0 but the app expects 9.9.9. "
            "Refusing to serve scores."
        ),
    )

    # (step, title, tree, record_bearing)
    specs = [
        ("1/8", "Overview — purpose, intended use and non-use", route(state, "/"), True),
        ("2/8", "Support Queue — ranked list, supportive bands", route(state, "/queue"), True),
        ("3/8", f"Student Review — record {record}", route(state, f"/review/{record}"), True),
        ("4/8", "Acknowledgement required before any action is recorded", ack_modal.modal(), True),
        ("5/8", "New Record Scoring — hypothetical, validated input", route(state, "/score"), True),
        ("6/8", "Equity Dashboard — aggregate fairness by group", route(state, "/equity"), True),
        ("7/8", "Model Card — version, limits, non-use policy", route(state, "/model-card"), False),
        ("8/8", "Version mismatch — no scores are served", blocked_layout(blocked), True),
    ]

    frames, findings, checked = [], [], 0
    for step, title, tree, record_bearing in specs:
        lines = body_lines(tree, skip_set, limit=28)
        if record_bearing:
            checked += 1
            for pattern in OUTCOME_TOKENS:
                for hit in re.findall(pattern, "\n".join(lines)):
                    findings.append(f"{step} {title}: {hit}")
        frames.append(frame(step, title, lines, state.disclaimer))

    if findings:
        print("PRIVACY CHECK FAILED — outcome labels visible in the demo:")
        for finding in findings:
            print(f"  {finding}")
        return 1
    print(
        f"privacy check: clean — no outcome label on any of the {checked} record-bearing "
        f"frames (the Model Card frame is exempt: it documents the target encoding and "
        f"carries no record data)"
    )

    palette = [f.convert("P", palette=Image.ADAPTIVE, colors=128) for f in frames]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    palette[0].save(
        out,
        save_all=True,
        append_images=palette[1:],
        duration=[4000] * len(palette),
        loop=0,
        optimize=True,
    )
    print(f"wrote {out}: {len(palette)} frames, {Path(out).stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:]))
