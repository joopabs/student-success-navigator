"""Build `reports/decks/business_deck.pptx` from the business deck outline (T073).

Mirrors `reports/decks/canvas/*.dc.html` — the same copy, the same palette (lifted from
`src/ssn/app/app.py`), and the same three figures pasted from their repository paths.
Every number traces to the file named in each slide's source strip; no number is re-drawn here.

python-pptx is NOT a project dependency and is deliberately not added to `requirements*.txt`
(it plays no part in the reproducible pipeline). Build in a throwaway environment:

    python -m venv /tmp/pptxenv && /tmp/pptxenv/bin/pip install python-pptx
    /tmp/pptxenv/bin/python reports/decks/canvas/build_pptx.py
"""

from __future__ import annotations

import pathlib
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = (pathlib.Path(sys.argv[1]) if len(sys.argv) > 1
       else ROOT / "reports" / "decks" / "business_deck.pptx")

# Palette lifted from src/ssn/app/app.py so the deck and the app read as one thing.
NAVY = RGBColor(0x1F, 0x3A, 0x5F)
INK = RGBColor(0x1D, 0x2A, 0x3A)
MUTED = RGBColor(0x5B, 0x6B, 0x7B)
RULE = RGBColor(0xD8, 0xDE, 0xE6)
PALE = RGBColor(0xE6, 0xEA, 0xEF)
PANEL = RGBColor(0xEE, 0xF1, 0xF5)
PAPER = RGBColor(0xFA, 0xFB, 0xFC)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
AMBER = RGBColor(0xB7, 0x79, 0x1F)
AMBER_L = RGBColor(0xFF, 0xF7, 0xE6)
AMBER_B = RGBColor(0xE0, 0xA8, 0x00)
AMBER_D = RGBColor(0x8A, 0x5A, 0x00)
GOLD = RGBColor(0xFF, 0xD9, 0x8A)
GREEN = RGBColor(0x2F, 0x6F, 0x4F)
BLUE = RGBColor(0x4C, 0x72, 0xB0)
RED = RGBColor(0xAA, 0x33, 0x33)
DIM = RGBColor(0xB8, 0xC6, 0xD8)
SUB = RGBColor(0xD6, 0xE0, 0xEC)
HAIR = RGBColor(0x3A, 0x54, 0x77)

DISPLAY = "Georgia"
BODY = "Calibri"
MONO = "Consolas"

RULE_HEX = "D8DEE6"
NAVY_HEX = "1F3A5F"


def px(v: float) -> Emu:
    """CSS px on the 1280x720 artboard -> EMU (the deck is authored at 96 px/inch)."""
    return Emu(int(round(v / 96 * 914400)))


def pt(v: float) -> Pt:
    return Pt(v * 0.75)


def slide(prs, bg=PAPER):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    fill = s.background.fill
    fill.solid()
    fill.fore_color.rgb = bg
    return s


def rect(s, x, y, w, h, fill=None, line=None, lw=1):
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(x), px(y), px(w), px(h))
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = px(lw)
    sh.shadow.inherit = False
    return sh


def tb(s, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    box = s.shapes.add_textbox(px(x), px(y), px(w), px(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    return tf


def para(tf, text, size, color=INK, bold=False, font=BODY, first=False,
         before=0, after=0, line=None, align=PP_ALIGN.LEFT, track=None):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    if before:
        p.space_before = pt(before)
    if after:
        p.space_after = pt(after)
    if line:
        p.line_spacing = line
    run = p.add_run()
    run.text = text
    f = run.font
    f.size = pt(size)
    f.bold = bold
    f.name = font
    f.color.rgb = color
    if track:
        run.font._rPr.set("spc", str(track))
    return p


def eyebrow(s, label, num):
    left = tb(s, 72, 56, 800, 18)
    para(left, label.upper(), 12, MUTED, bold=True, first=True, track=170)
    right = tb(s, 408, 56, 800, 18)
    para(right, f"{num:02d} / 10", 12, MUTED, bold=True, first=True,
         align=PP_ALIGN.RIGHT, track=170)
    rect(s, 72, 82, 1136, 2, fill=NAVY)


def source(s, text):
    rect(s, 72, 664, 1136, 1, fill=RULE)
    para(tb(s, 72, 676, 1136, 16), text, 12, MUTED, font=MONO, first=True)


def headline(s, text, y, size=36, w=1136):
    para(tb(s, 72, y, w, 160), text, size, NAVY, bold=True, font=DISPLAY,
         first=True, line=1.16)


def label(s, x, y, w, text, color=MUTED):
    para(tb(s, x, y, w, 16), text.upper(), 11, color, bold=True, first=True, track=150)


def border(cell, color=RULE_HEX, width=1.0, edge="bottom"):
    """Hairline cell border — python-pptx exposes no border API, so write the XML."""
    tag = {"left": "a:lnL", "right": "a:lnR", "top": "a:lnT", "bottom": "a:lnB"}[edge]
    tcPr = cell._tc.get_or_add_tcPr()
    for existing in tcPr.findall(qn(tag)):
        tcPr.remove(existing)
    ln = tcPr.makeelement(qn(tag), {"w": str(int(width * 12700)), "cap": "flat",
                                    "cmpd": "sng", "algn": "ctr"})
    solid = ln.makeelement(qn("a:solidFill"), {})
    clr = ln.makeelement(qn("a:srgbClr"), {"val": color})
    solid.append(clr)
    ln.append(solid)
    tcPr.insert(0, ln)


def table(s, x, y, col_w, heights):
    shp = s.shapes.add_table(len(heights), len(col_w), px(x), px(y),
                             px(sum(col_w)), px(sum(heights)))
    t = shp.table
    t.first_row = False
    t.horz_banding = False
    for i, w in enumerate(col_w):
        t.columns[i].width = px(w)
    for i, h in enumerate(heights):
        t.rows[i].height = px(h)
    return t


def cell(t, r, c, text, size=16, color=INK, bold=False, fill=WHITE,
         align=PP_ALIGN.LEFT, font=BODY, sub=None, sub_color=None, line=1.3):
    cl = t.cell(r, c)
    cl.fill.solid()
    cl.fill.fore_color.rgb = fill
    cl.margin_left = px(0 if align == PP_ALIGN.LEFT else 10)
    cl.margin_right = px(10 if align == PP_ALIGN.LEFT else 0)
    cl.margin_top = px(6)
    cl.margin_bottom = px(6)
    cl.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf = cl.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line
    run = p.add_run()
    run.text = text
    f = run.font
    f.size = pt(size)
    f.bold = bold
    f.name = font
    f.color.rgb = color
    if sub:
        p2 = tf.add_paragraph()
        p2.alignment = align
        run2 = p2.add_run()
        run2.text = sub
        f2 = run2.font
        f2.size = pt(11)
        f2.name = font
        f2.color.rgb = sub_color or MUTED
    return cl


def head_cell(t, c, text, sub=None, align=PP_ALIGN.LEFT, color=MUTED):
    cl = cell(t, 0, c, text.upper(), size=11, color=color, bold=True, fill=PAPER,
              align=align, sub=sub, sub_color=color, line=1.25)
    for run in cl.text_frame.paragraphs[0].runs:
        run.font._rPr.set("spc", "130")
    border(cl, NAVY_HEX, 2.0)
    return cl


# --------------------------------------------------------------------------------------

prs = Presentation()
prs.slide_width = px(1280)
prs.slide_height = px(720)

# ---- 01 Title -----------------------------------------------------------------------
s = slide(prs, NAVY)
rect(s, 88, 92, 56, 3, fill=AMBER_B)
para(tb(s, 156, 87, 700, 18), "DECISION-SUPPORT PROTOTYPE", 13, DIM, bold=True,
     first=True, track=200)
para(tb(s, 88, 152, 960, 180), "Student Success Navigator", 76, WHITE,
     font=DISPLAY, first=True, line=1.04)
para(tb(s, 88, 330, 900, 90), "Earlier, fairer, supportive outreach after the first semester",
     30, SUB, font=DISPLAY, first=True, line=1.35)
para(tb(s, 88, 432, 780, 60),
     "A decision-support prototype built on one institution's public data "
     "(UCI, CC BY 4.0) — illustrative, not deployed.", 17, DIM, first=True, line=1.6)
rect(s, 88, 640, 1104, 1, fill=HAIR)
para(tb(s, 88, 656, 600, 18), "model version 1.0.0", 13, DIM, font=MONO, first=True)
para(tb(s, 592, 656, 600, 18), "reports/model_card.md", 13, DIM, font=MONO, first=True,
     align=PP_ALIGN.RIGHT)

# ---- 02 The opportunity -------------------------------------------------------------
s = slide(prs)
eyebrow(s, "The opportunity", 2)
headline(s, "Many students who leave show academic warning signs in their first semester",
         116, size=40, w=1000)
para(tb(s, 72, 246, 520, 92), "32%", 82, NAVY, bold=True, font=DISPLAY, first=True,
     line=1.0)
para(tb(s, 72, 348, 470, 60),
     "of students in the historical dataset did not complete — 1,421 of 4,424.",
     19, INK, first=True, line=1.5)
rect(s, 72, 424, 224, 26, fill=PANEL, line=RULE)
para(tb(s, 84, 431, 210, 16), "MEASURED · THIS DATASET", 11, MUTED, bold=True,
     first=True, track=130)
rect(s, 616, 246, 2, 236, fill=RULE)
para(tb(s, 656, 246, 552, 130),
     "Advisers have limited time to reach them. The opportunity is to prioritise "
     "voluntary, supportive conversations with the students most likely to benefit — "
     "within advisers' existing time.", 19, INK, first=True, line=1.55)
rect(s, 656, 388, 552, 94, fill=AMBER_L)
rect(s, 656, 388, 4, 94, fill=AMBER_B)
label(s, 676, 404, 500, "What this deck does not claim", AMBER_D)
para(tb(s, 676, 428, 512, 50),
     "That outreach reduces dropout. That is the hypothesis a pilot would test.",
     16, INK, first=True, line=1.5)
source(s, "reports/tables/profile_target.csv")

# ---- 03 How it would be used --------------------------------------------------------
s = slide(prs)
eyebrow(s, "How it would be used", 3)
headline(s, "The adviser stays the decision-maker at every step", 116)
steps = [
    ("Trigger", "End of semester 1", None, MUTED, RULE),
    ("Model", "Support-priority score", None, BLUE, RULE),
    ("Shortlist", "Support Queue", "top-K list, supportive bands", BLUE, RULE),
    ("Human", "Adviser reviews each record", None, AMBER, AMBER),
    ("Outcome", "Conversation, referral or dismiss", None, AMBER, AMBER),
]
bw, gap = 208, 24
for i, (kicker, title, note, accent, edge) in enumerate(steps):
    x = 72 + i * (bw + gap)
    rect(s, x, 180, bw, 96, fill=WHITE, line=edge)
    rect(s, x, 180, bw, 3, fill=accent)
    label(s, x + 14, 194, bw - 28, kicker, accent)
    para(tb(s, x + 14, 214, bw - 28, 52), title, 16, INK, bold=True, first=True, line=1.35)
    if note:
        para(tb(s, x + 14, 252, bw - 28, 18), note, 13, MUTED, first=True)
    if i < len(steps) - 1:
        para(tb(s, x + bw, 216, gap, 20), "→", 18, RGBColor(0x9A, 0xA8, 0xB8),
             first=True, align=PP_ALIGN.CENTER)
rect(s, 72, 300, 1136, 46, fill=NAVY)
tf = tb(s, 92, 314, 1096, 22)
p = tf.paragraphs[0]
for text, color, bold in [("The decision is recorded locally — ", WHITE, False),
                          ("nothing feeds back into the model.", GOLD, True)]:
    run = p.add_run()
    run.text = text
    run.font.size = pt(16)
    run.font.bold = bold
    run.font.name = BODY
    run.font.color.rgb = color
guards = [
    "Human acknowledgement is required before any action is recorded.",
    "No student identifiers and no outcome labels are shown to advisers.",
    "Neutral academic language only.",
]
for i, text in enumerate(guards):
    x = 72 + i * 384
    label(s, x, 386, 352, f"Safeguard {i + 1:02d}", GREEN)
    para(tb(s, x, 410, 352, 80), text, 15, INK, first=True, line=1.45)
source(s, "specs/001-dropout-risk-navigator/contracts/app-pages.md")

# ---- 04 What the score is made of ---------------------------------------------------
s = slide(prs)
eyebrow(s, "What the score is made of", 4)
headline(s, "The score reflects how the first semester went, not who the student is",
         114, w=1000)
label(s, 72, 230, 700, "What goes in")
para(tb(s, 72, 252, 740, 60),
     "Enrollment details and first-semester results only — 21 columns plus 7 derived "
     "indicators, such as the share of first-semester units passed.", 17, INK,
     first=True, line=1.5)
label(s, 72, 336, 700, "Top drivers · measured, SHAP", BLUE)
drivers = ["sem1_approval_rate", "Curricular units 1st sem (approved)",
           "Curricular units 1st sem (grade)", "grade_diff_vs_admission"]
for i, name in enumerate(drivers):
    y = 362 + i * 30
    para(tb(s, 72, y, 30, 18), f"{i + 1:02d}", 12, RGBColor(0x9A, 0xA8, 0xB8),
         font=MONO, first=True)
    para(tb(s, 104, y - 1, 660, 20), name, 16, INK, bold=True, first=True)
    if i < len(drivers) - 1:
        rect(s, 72, y + 22, 740, 1, fill=PALE)
rect(s, 72, 496, 740, 96, fill=PANEL, line=RULE)
label(s, 90, 512, 700, "Never inputs", NAVY)
para(tb(s, 90, 534, 706, 60),
     "Anything from the second semester · financial-status flags with unclear timing · "
     "gender, age, nationality, marital status, international status, special needs.",
     15, INK, first=True, line=1.5)
s.shapes.add_picture(str(ROOT / "reports/explainability/shap_global_bar.png"),
                     px(868), px(230), width=px(340))
para(tb(s, 868, 604, 340, 34), "Full ranking: shap_global_importance.csv", 12, MUTED,
     first=True, line=1.4)
source(s, "reports/explainability/shap_global_importance.csv · "
          "reports/explainability/shap_global_bar.png")

# ---- 05 Measured performance --------------------------------------------------------
s = slide(prs)
eyebrow(s, "Measured performance", 5)
headline(s, "Held-out test cohort, evaluated once", 114)
para(tb(s, 72, 160, 700, 20), "885 students · 284 of them eventually dropped out",
     15, MUTED, first=True)
t = table(s, 72, 200, [340, 168, 164], [40, 52, 52, 52])
head_cell(t, 0, "Measure")
head_cell(t, 1, "Final model", align=PP_ALIGN.RIGHT, color=NAVY)
head_cell(t, 2, "Chance baseline", align=PP_ALIGN.RIGHT)
rows = [("Ranking quality (PR-AUC)", "0.82", "0.32"),
        ("Of a top-50 list, later dropped out (Precision@K)", "96%", "42%"),
        ("Calibration error (lower is better)", "0.034", "—")]
for r, (measure, final, base) in enumerate(rows, start=1):
    for cl in [
        cell(t, r, 0, measure, size=15),
        cell(t, r, 1, final, size=22, color=NAVY, bold=True, align=PP_ALIGN.RIGHT),
        cell(t, r, 2, base, size=16, color=MUTED, align=PP_ALIGN.RIGHT),
    ]:
        border(cl)
rect(s, 72, 412, 3, 76, fill=AMBER)
para(tb(s, 90, 412, 582, 80),
     "When the model puts a student on a 50-person list, about 96 in 100 later dropped "
     "out. For a random list it would be about 42 in 100.", 19, INK, font=DISPLAY,
     first=True, line=1.5)
rect(s, 72, 512, 672, 56, fill=AMBER_L)
rect(s, 72, 512, 4, 56, fill=AMBER_B)
para(tb(s, 90, 528, 640, 40),
     "Measured on one institution's historical data. A local pilot must re-measure.",
     15, INK, first=True, line=1.5)
s.shapes.add_picture(str(ROOT / "reports/figures/test_pr_curve.png"),
                     px(788), px(200), width=px(420))
source(s, "reports/tables/test_metrics_all_models.csv · reports/figures/test_pr_curve.png")

# ---- 06 Outreach reach --------------------------------------------------------------
s = slide(prs)
eyebrow(s, "Outreach reach", 6)
rect(s, 0, 0, 1280, 8, fill=AMBER_B)
rect(s, 72, 112, 232, 30, fill=AMBER_L, line=AMBER_B)
para(tb(s, 86, 120, 210, 16), "ILLUSTRATIVE ASSUMPTIONS", 12, AMBER_D, bold=True,
     first=True, track=180)
para(tb(s, 322, 121, 886, 20),
     "The two columns on the right are measured; the window and the number contacted "
     "are assumed.", 14, MUTED, first=True)
headline(s, "Reach is limited by adviser time, not by the model", 162)
t = table(s, 72, 232, [200, 168, 216, 212], [58, 54, 54, 54])
head_cell(t, 0, "Outreach window", sub="illustrative", color=AMBER_D)
head_cell(t, 1, "Students contacted", sub="illustrative", align=PP_ALIGN.RIGHT,
          color=AMBER_D)
head_cell(t, 2, "Share of eventual dropouts reached", sub="measured recall",
          align=PP_ALIGN.RIGHT, color=NAVY)
head_cell(t, 3, "Contacted who did drop out", sub="measured precision",
          align=PP_ALIGN.RIGHT, color=NAVY)
reach = [("2 weeks", "20", "7%", "95%", False),
         ("5 weeks", "50", "17%", "96%", True),
         ("10 weeks", "100", "33%", "93%", False)]
for r, (window, contacted, recall, precision, hi) in enumerate(reach, start=1):
    bg = AMBER_L if hi else WHITE
    for cl in [
        cell(t, r, 0, window, size=16, bold=hi, fill=bg),
        cell(t, r, 1, contacted, size=16, bold=hi, fill=bg, align=PP_ALIGN.RIGHT),
        cell(t, r, 2, recall, size=19, color=NAVY, bold=True, fill=bg,
             align=PP_ALIGN.RIGHT),
        cell(t, r, 3, precision, size=19, color=NAVY, bold=True, fill=bg,
             align=PP_ALIGN.RIGHT),
    ]:
        border(cl)
para(tb(s, 72, 474, 796, 40),
     "More weeks, more students reached — and the list stays precise.", 19, INK,
     font=DISPLAY, first=True, line=1.5)
rect(s, 908, 232, 300, 132, fill=WHITE, line=RULE)
rect(s, 908, 232, 300, 3, fill=AMBER)
label(s, 926, 248, 270, "The assumption", AMBER_D)
para(tb(s, 926, 270, 268, 90),
     "10 conversations per adviser-week, over a 5-week window — 50 students from a "
     "cohort of 885. Illustrative assumption only.", 15, INK, first=True, line=1.5)
rect(s, 908, 380, 300, 130, fill=PANEL, line=RULE)
label(s, 926, 396, 270, "Deliberately absent", NAVY)
para(tb(s, 926, 418, 268, 70),
     "No figure here is converted to money. No cost or saving data exists in this "
     "project, so none is presented.", 15, INK, first=True, line=1.5)
source(s, "reports/tables/test_recall_precision_at_k.csv · "
          "284 eventual dropouts in the 885-student test cohort")

# ---- 07 Safeguards ------------------------------------------------------------------
s = slide(prs)
eyebrow(s, "Safeguards", 7)
headline(s, "Four safeguards built into the design", 116)
cards = [
    (GREEN, "Leakage-safe by construction",
     "Only information available at the prediction point enters the model — the end of "
     "semester one. Enforced by tests."),
    (GREEN, "Sensitive attributes stay out",
     "Never model inputs and never shown as reasons. They are used only to audit "
     "outcomes by group. Enforced by tests."),
    (AMBER, "A human decides, every time",
     "Acknowledgement is required before any action is recorded. Advisers can dismiss "
     "or override. Actions stay local and never feed back into the model."),
    (AMBER, "A written non-use policy",
     "No automated or adverse decision on admission, enrollment, aid, grades, "
     "discipline or housing. Set out in the project constitution."),
]
for i, (accent, title, body) in enumerate(cards):
    x = 72 + (i % 2) * 588
    y = 196 + (i // 2) * 176
    rect(s, x, y, 548, 152, fill=WHITE, line=RULE)
    rect(s, x, y, 3, 152, fill=accent)
    para(tb(s, x + 24, y + 20, 500, 24), title, 18, NAVY, bold=True, first=True)
    para(tb(s, x + 24, y + 54, 500, 90), body, 16, INK, first=True, line=1.5)
source(s, ".specify/memory/constitution.md · reports/model_card.md")

# ---- 08 What the fairness audit found -----------------------------------------------
s = slide(prs)
eyebrow(s, "What the fairness audit found", 8)
headline(s, "Younger students who leave are under-reached", 114)
t = table(s, 72, 176, [386, 284, 466], [50, 54, 54])
head_cell(t, 0, "Group comparison · held-out cohort")
head_cell(t, 1, "Selection gap")
head_cell(t, 2, "Among students who did drop out, chance of being on the list")
fair = [("Women vs men", "5.0% vs 9.0%", "20% vs 19% — near equal", False),
        ("Age 17–19 vs 35+", "2.0% vs 24.7%", "10% vs 50%", True)]
for r, (group, gap, chance, hi) in enumerate(fair, start=1):
    bg = AMBER_L if hi else WHITE
    for cl in [
        cell(t, r, 0, group, size=17, bold=hi, fill=bg),
        cell(t, r, 1, gap, size=17, bold=hi, fill=bg),
        cell(t, r, 2, chance, size=21 if hi else 17,
             color=AMBER_D if hi else INK, bold=hi, fill=bg),
    ]:
        border(cl)
s.shapes.add_picture(str(ROOT / "reports/fairness/selection_rates.png"),
                     px(72), px(360), width=px(440))
para(tb(s, 548, 360, 660, 70),
     "The list reflects historical patterns in the data. Younger students who leave "
     "are under-reached.", 18, INK, first=True, line=1.5)
rect(s, 548, 452, 660, 116, fill=WHITE, line=RULE)
rect(s, 548, 452, 660, 3, fill=GREEN)
label(s, 568, 470, 620, "Recommended response", GREEN)
para(tb(s, 568, 494, 622, 70),
     "An adviser-side rule — reserve part of the outreach list for first-years — "
     "rather than a change to the model.", 16, INK, first=True, line=1.5)
source(s, "reports/fairness/group_metrics.csv · reports/fairness/selection_rates.png · "
          "full discussion in reports/bias_fairness_analysis.md")

# ---- 09 Risks and governance --------------------------------------------------------
s = slide(prs)
eyebrow(s, "Risks and governance", 9)
headline(s, "Risks, governance, and what a pilot would need", 116)
columns = [
    (RED, "The risks", [
        "Historical bias in the recorded outcomes",
        "Proxy features — parental background, application route",
        "Single-institution scope",
        "Small subgroups",
        "Feedback loops, if the model were ever retrained on outreach data"]),
    (GREEN, "Already in place", [
        "A written constitution and a model card",
        "A published fairness audit and a limitations statement",
        "A reproducible pipeline — a fresh-environment re-run gives zero deltas",
        "CI on every change, and a version-checked artifact",
        "A local action log"]),
    (NAVY, "What a pilot would need", [
        "Institutional approval",
        "A local data agreement",
        "Re-training and a fresh audit on local data",
        "Adviser training",
        "A standing review cadence for the Equity Dashboard"]),
]
for i, (accent, title, items) in enumerate(columns):
    x = 72 + i * 392
    para(tb(s, x, 200, 352, 18), title.upper(), 12, accent, bold=True, first=True,
         track=140)
    rect(s, x, 226, 352, 2, fill=accent)
    y = 244
    for j, item in enumerate(items):
        h = 44 if len(item) < 46 else 66
        para(tb(s, x, y, 352, h), item, 15, INK, first=True, line=1.45)
        y += h
        if j < len(items) - 1:
            rect(s, x, y - 10, 352, 1, fill=PALE)
source(s, "reports/limitations.md · reports/model_card.md · "
          ".specify/memory/constitution.md")

# ---- 10 Next steps and the ask ------------------------------------------------------
s = slide(prs)
eyebrow(s, "Next steps and the ask", 10)
headline(s, "Three decisions before any local build", 116)
steps = [
    ("01", "Decide whether to pilot with local data",
     "Under the governance set out on the previous slide — nothing here is a "
     "deployment decision."),
    ("02", "Resolve the open data question with the data owner",
     "The timing of the financial-status fields is unclear, so they are excluded "
     "today. That must be settled before any local build."),
    ("03", "Design the pilot to measure what this project cannot",
     "Whether outreach changes outcomes — the model does not show this — and how the "
     "list's composition by group moves each cycle."),
]
y = 194
for num, title, body in steps:
    para(tb(s, 72, y, 60, 40), num, 30, AMBER, bold=True, font=DISPLAY, first=True)
    para(tb(s, 138, y - 2, 1070, 26), title, 19, NAVY, bold=True, first=True)
    para(tb(s, 138, y + 28, 1060, 50), body, 16, INK, first=True, line=1.5)
    y += 92
    if num != "03":
        rect(s, 72, y - 16, 1136, 1, fill=RULE)
rect(s, 72, 484, 1136, 153, fill=NAVY)
rect(s, 96, 512, 2, 72, fill=AMBER_B)
para(tb(s, 118, 510, 300, 18), "THE ASK", 11, GOLD, bold=True, first=True, track=180)
para(tb(s, 118, 536, 1050, 70),
     "Sponsorship for a time-boxed pilot with an equity review checkpoint — not a "
     "deployment decision.", 25, WHITE, font=DISPLAY, first=True, line=1.4)
source(s, "reports/final_report.md · reports/model_card.md · model version 1.0.0")

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(OUT)
print(f"wrote {OUT} — {len(prs.slides._sldIdLst)} slides, "
      f"{OUT.stat().st_size / 1024:.0f} KB")
