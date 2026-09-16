"""Build `reports/decks/technical_deck.pptx` from `notebooks/90_technical_deck.ipynb` (T073).

The same 12 slides as `reports/decks/technical_deck.slides.html`, in an approved submission
format (`CAPSTONE_BRIEF.md` section 8 allows .pdf/.doc/.pptx/.ppt only). The reveal.js export
scales tall figures to the viewport and clips them; here each figure is placed at its own
aspect ratio inside a reserved band, so nothing is cropped.

Palette and helpers mirror `build_pptx.py` so the two decks and the app read as one system.
Every number is copied from the notebook, which reads them from files under `reports/`.

python-pptx is NOT a project dependency and is deliberately not added to `requirements*.txt`
(it plays no part in the reproducible pipeline). Build in a throwaway environment:

    python -m venv /tmp/pptxenv && /tmp/pptxenv/bin/pip install python-pptx
    /tmp/pptxenv/bin/python reports/decks/canvas/build_technical_pptx.py
"""

from __future__ import annotations

import pathlib
import re
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = (pathlib.Path(sys.argv[1]) if len(sys.argv) > 1
       else ROOT / "reports" / "decks" / "technical_deck.pptx")

# Palette lifted from src/ssn/app/app.py so the deck and the app read as one thing.
NAVY = RGBColor(0x1F, 0x3A, 0x5F)
INK = RGBColor(0x1D, 0x2A, 0x3A)
MUTED = RGBColor(0x5B, 0x6B, 0x7B)
RULE = RGBColor(0xD8, 0xDE, 0xE6)
PANEL = RGBColor(0xEE, 0xF1, 0xF5)
PAPER = RGBColor(0xFA, 0xFB, 0xFC)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
AMBER = RGBColor(0xB7, 0x79, 0x1F)
AMBER_L = RGBColor(0xFF, 0xF7, 0xE6)
AMBER_B = RGBColor(0xE0, 0xA8, 0x00)
GOLD = RGBColor(0xFF, 0xD9, 0x8A)
RED = RGBColor(0xAA, 0x33, 0x33)
SUB = RGBColor(0xD6, 0xE0, 0xEC)

DISPLAY = "Georgia"
BODY = "Calibri"
MONO = "Consolas"

RULE_HEX = "D8DEE6"
NAVY_HEX = "1F3A5F"

N_SLIDES = 12


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


def rich(p, text, size, color=INK, font=BODY):
    """Add runs for one paragraph, honouring **bold** and `mono` spans from the notebook."""
    for piece in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if not piece:
            continue
        bold = piece.startswith("**")
        mono = piece.startswith("`")
        body = piece[2:-2] if bold else piece[1:-1] if mono else piece
        run = p.add_run()
        run.text = body
        f = run.font
        f.size = pt(size - 1 if mono else size)
        f.bold = bold
        f.name = MONO if mono else font
        f.color.rgb = NAVY if bold else color
    return p


def bullets(s, x, y, w, h, items, size=15, line=1.4, gap=7):
    """One text frame for the whole list so PowerPoint flows the wrapping itself."""
    tf = tb(s, x, y, w, h)
    for i, text in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = line
        if i:
            p.space_before = pt(gap)
        dash = p.add_run()
        dash.text = "—  "
        dash.font.size = pt(size)
        dash.font.name = BODY
        dash.font.color.rgb = RULE
        rich(p, text, size)
    return tf


def eyebrow(s, label, num):
    left = tb(s, 72, 56, 800, 18)
    para(left, label.upper(), 12, MUTED, bold=True, first=True, track=170)
    right = tb(s, 408, 56, 800, 18)
    para(right, f"{num:02d} / {N_SLIDES}", 12, MUTED, bold=True, first=True,
         align=PP_ALIGN.RIGHT, track=170)
    rect(s, 72, 82, 1136, 2, fill=NAVY)


def source(s, text):
    rect(s, 72, 664, 1136, 1, fill=RULE)
    para(tb(s, 72, 676, 1136, 16), text, 11, MUTED, font=MONO, first=True)


def headline(s, text, y=100, size=31, w=1136):
    para(tb(s, 72, y, w, 90), text, size, NAVY, bold=True, font=DISPLAY,
         first=True, line=1.16)


def border(cell_, color=RULE_HEX, width=1.0, edge="bottom"):
    """Hairline cell border — python-pptx exposes no border API, so write the XML."""
    tag = {"left": "a:lnL", "right": "a:lnR", "top": "a:lnT", "bottom": "a:lnB"}[edge]
    tcPr = cell_._tc.get_or_add_tcPr()
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


def cell(t, r, c, text, size=15, color=INK, bold=False, fill=WHITE,
         align=PP_ALIGN.LEFT, font=BODY, line=1.25):
    cl = t.cell(r, c)
    cl.fill.solid()
    cl.fill.fore_color.rgb = fill
    cl.margin_left = px(12 if align == PP_ALIGN.LEFT else 10)
    cl.margin_right = px(10 if align == PP_ALIGN.LEFT else 12)
    cl.margin_top = px(6)
    cl.margin_bottom = px(6)
    cl.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf = cl.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line
    rich(p, text, size, color=color, font=font)
    if bold:
        for run in p.runs:
            run.font.bold = True
    border(cl)
    return cl


def head_cell(t, c, text, align=PP_ALIGN.LEFT):
    cl = cell(t, 0, c, text.upper(), size=11, color=MUTED, bold=True, fill=PAPER,
              align=align, line=1.2)
    for run in cl.text_frame.paragraphs[0].runs:
        run.font._rPr.set("spc", "130")
    border(cl, NAVY_HEX, 2.0)
    return cl


def figure(s, name, x, y, h):
    """Place a figure at its true aspect ratio; returns the width used."""
    from PIL import Image
    path = ROOT / name
    with Image.open(path) as im:
        w = h * im.size[0] / im.size[1]
    s.shapes.add_picture(str(path), px(x), px(y), px(w), px(h))
    return w


def note(s, x, y, w, h, text, size=13):
    rect(s, x, y, w, h, fill=AMBER_L)
    rect(s, x, y, 3, h, fill=AMBER_B)
    tf = tb(s, x + 18, y + 12, w - 34, h - 20)
    rich(tf.paragraphs[0], text, size, color=AMBER)
    tf.paragraphs[0].line_spacing = 1.35


prs = Presentation()
prs.slide_width = px(1280)
prs.slide_height = px(720)

# ---- 01 Title -----------------------------------------------------------------------------
s = slide(prs, NAVY)
rect(s, 88, 92, 56, 3, fill=AMBER_B)
para(tb(s, 88, 118, 1000, 20), "TECHNICAL PRESENTATION", 12, GOLD, bold=True,
     first=True, track=180)
para(tb(s, 88, 158, 1104, 190),
     "Fair and Explainable Student Dropout Risk Prediction for Early Academic Support",
     40, WHITE, bold=True, font=DISPLAY, first=True, line=1.14)
rect(s, 88, 372, 1104, 1, fill=HAIR if (HAIR := RGBColor(0x3A, 0x54, 0x77)) else None)
tfq = tb(s, 88, 398, 1104, 60)
rich(tfq.paragraphs[0],
     "**Question.** At the end of a student's first semester, can we rank students so that a "
     "small, voluntary adviser outreach list reaches those most likely to leave, using only "
     "information available at that point, explainably and with a fairness audit?", 16,
     color=SUB)
tfq.paragraphs[0].line_spacing = 1.45
for run in tfq.paragraphs[0].runs:
    if run.font.bold:
        run.font.color.rgb = WHITE
tfa = tb(s, 88, 494, 1104, 90)
rich(tfa.paragraphs[0],
     "**Answer in one line.** A calibrated random-forest pipeline on 21 enrollment-time and "
     "first-semester features reaches held-out PR-AUC 0.817 (base rate 0.321), fills an "
     "illustrative outreach list at 96% precision, and shows an equal-opportunity gap by age "
     "that advisers must compensate for.", 16, color=SUB)
tfa.paragraphs[0].line_spacing = 1.45
for run in tfa.paragraphs[0].runs:
    if run.font.bold:
        run.font.color.rgb = WHITE
para(tb(s, 88, 624, 1104, 40),
     "Student Success Navigator · v1.0.0 · every number is read from files under reports/; "
     "nothing on these slides is typed by hand", 11,
     RGBColor(0x9F, 0xB4, 0xCE), font=MONO, first=True)

# ---- 02 Problem framing -------------------------------------------------------------------
s = slide(prs)
eyebrow(s, "Problem framing", 2)
headline(s, "Ranking for a fixed-capacity outreach list, not a verdict on a student")
bullets(s, 72, 168, 1136, 440, [
    "**Unit of analysis:** one student enrollment record · **Prediction point:** end of first "
    "semester",
    "**Task:** binary classification, `is_dropout` = 1 where source Target = Dropout "
    "(Enrolled and Graduate = 0)",
    "**Use:** decision support for *voluntary, supportive* adviser outreach within a fixed "
    "capacity",
    "**Non-use:** no automated or adverse decision about admission, enrollment, aid, grades, "
    "discipline, housing",
    "**Primary metric:** PR-AUC (imbalance: positive rate 0.321) · **Intervention metric:** "
    "Recall@K and Precision@K",
    "**Capacity assumption (ILLUSTRATIVE):** 10 students/week × 5 weeks = K 50 per cohort of 885",
    "Governance: constitution with 12 principles and 10 quality gates; Spec Kit spec → plan "
    "→ 94 tasks",
], size=16, gap=11)
source(s, "specs/001-dropout-risk-navigator/ · .specify/memory/constitution.md · configs/base.yaml")

# ---- 03 Dataset ---------------------------------------------------------------------------
s = slide(prs)
eyebrow(s, "Dataset", 3)
headline(s, "UCI 697 — one institution, 4,424 records, every code verified")
bullets(s, 72, 168, 1136, 430, [
    "UCI ML Repository 697, *Predict Students' Dropout and Academic Success* "
    "(Realinho et al., 2021), **CC BY 4.0**, DOI 10.24432/C5MC89",
    "One Portuguese higher-education institution; **4,424** records × 36 features + Target; "
    "0 missing, 0 duplicates, 0 undocumented codes",
    "Target: Graduate 2,209 · Dropout 1,421 · Enrolled 794 → positive rate 0.321",
    "Every categorical encoding copied from the UCI variables table and verified against "
    "observed codes (22 coded columns, including Gender 1 = male, 0 = female)",
    "Stratified 80/20 split, seed 42: train **3539** · test **885** (evaluated once)",
], size=16, gap=11)
note(s, 72, 536, 1136, 72,
     "Not representative of Philippine or other institutions; outcomes are historical and may "
     "encode institutional inequities.")
source(s, "reports/data_overview.md · reports/tables/profile_*.csv · configs/features.yaml")

# ---- 04 Leakage controls ------------------------------------------------------------------
s = slide(prs)
eyebrow(s, "Leakage controls", 4)
headline(s, "The feature-availability list decides what the model may see")
t = table(s, 72, 164, [656, 150, 330], [46, 42, 42, 42, 42, 42])
head_cell(t, 0, "Class")
head_cell(t, 1, "Columns", align=PP_ALIGN.RIGHT)
head_cell(t, 2, "Model input?")
rows = [
    ("Enrollment-time features", "15", "yes", INK, WHITE),
    ("First-semester features", "6", "yes", INK, WHITE),
    ("Second-semester (after prediction point)", "6", "**no**", INK, PANEL),
    ("Financial status, undocumented timing (Debtor, Tuition fees, Scholarship holder)",
     "3", "**no** (ambiguous)", INK, PANEL),
    ("Sensitive attributes (gender, age, nationality, international, marital, needs)",
     "6", "**no** (audit only)", INK, PANEL),
]
for i, (name, n, allowed, col, bg) in enumerate(rows, start=1):
    cell(t, i, 0, name, color=col, fill=bg)
    cell(t, i, 1, n, align=PP_ALIGN.RIGHT, fill=bg, bold=True)
    cell(t, i, 2, allowed, fill=bg, color=MUTED)
bullets(s, 72, 436, 1136, 190, [
    "Enforced by `configs/features.yaml`, `project_features` / `assert_frame_allowed`, and "
    "tests that spy on every parquet read",
    "**Cost of the guard, measured:** including the 3 ambiguous columns would add 0.036–0.039 "
    "CV PR-AUC (`ablation_ambiguous.csv`) — a gain that may be leakage, so they stay out",
    "Excluding the 6 sensitive attributes costs at most 0.0065 PR-AUC (`ablation_sensitive.csv`)",
], size=15, gap=9)
source(s, "configs/features.yaml · reports/tables/ablation_ambiguous.csv · ablation_sensitive.csv")

# ---- 05 EDA -------------------------------------------------------------------------------
s = slide(prs)
eyebrow(s, "EDA (training split only)", 5)
headline(s, "First-semester performance carries the signal", size=29)
fw = figure(s, "reports/figures/eda_correlation_spearman.png", 72, 168, 468)
bullets(s, 72 + fw + 44, 180, 1208 - (72 + fw + 44) - 72, 420, [
    "First-semester approvals, approval rate and grade carry the strongest associations "
    "with dropout",
    "138 training records have zero first-semester units enrolled (rate features undefined "
    "→ imputed inside CV)",
    "Sensitive-group base rates differ widely (e.g. dropout rate 46.1% male vs 24.5% female "
    "on test): context for the audit, never a model input",
], size=15, gap=13)
source(s, "reports/figures/eda_correlation_spearman.png · "
       "reports/eda_feature_engineering_report.md")

# ---- 06 Features, selection, PCA ----------------------------------------------------------
s = slide(prs)
eyebrow(s, "Features, selection, PCA", 6)
headline(s, "Selection and PCA were compared, then declined on evidence", size=29)
bullets(s, 72, 158, 1136, 215, [
    "**7 stateless engineered features** from allow-listed inputs: approval rate, evaluation "
    "participation rate, non-evaluation rate, grade change vs admission (scales matched), "
    "credited share, load, any-approved",
    "Preprocessing = median impute · scale · one-hot → **207** columns; all fitting inside "
    "CV folds",
    "**Selection:** mutual-information filter and L1-logistic embedded selectors over "
    "k ∈ {10…all}; keeping all 207 scored highest (0.818), embedded k = 30 within one std "
    "(0.811) → carried as a tuned variant, not imposed",
    "**PCA:** 42 components for 95% variance; PCA pipeline 0.801 vs 0.818 without → retained "
    "for analysis/visualisation only",
], size=15, gap=8)
fw = figure(s, "reports/figures/pca_scree.png", 362, 386, 268)
source(s, "reports/tables/selection_decision.json · pca_vs_nopca_cv.csv · "
       "reports/figures/pca_scree.png")

# ---- 07 Model comparison ------------------------------------------------------------------
s = slide(prs)
eyebrow(s, "Model comparison", 7)
headline(s, "5-fold stratified CV, seed 42 — all three within one CV std")
t = table(s, 72, 158, [386, 176, 140, 158, 138, 138], [48, 42, 42, 42, 42])
for i, (h, al) in enumerate([("Model (class-weighted, all features)", PP_ALIGN.LEFT),
                             ("PR-AUC", PP_ALIGN.RIGHT), ("ROC-AUC", PP_ALIGN.RIGHT),
                             ("Precision@K", PP_ALIGN.RIGHT), ("Brier", PP_ALIGN.RIGHT),
                             ("ECE", PP_ALIGN.RIGHT)]):
    head_cell(t, i, h, align=al)
mrows = [
    ("Dummy (prior)", "0.321", "0.500", "0.33", "0.218", "0.001", PANEL),
    ("Logistic regression", "0.818 ± 0.017", "0.878", "0.97", "0.134", "0.096", WHITE),
    ("Random forest", "**0.807 ± 0.009**", "0.872", "0.96", "0.126", "**0.032**", AMBER_L),
    ("HistGradientBoosting", "0.811 ± 0.014", "0.869", "0.98", "0.132", "0.067", WHITE),
]
for i, (name, a, b, c, d, e, bg) in enumerate(mrows, start=1):
    cell(t, i, 0, name, fill=bg, bold=(bg is AMBER_L))
    for j, v in enumerate((a, b, c, d, e), start=1):
        cell(t, i, j, v, align=PP_ALIGN.RIGHT, fill=bg)
bullets(s, 72, 388, 1136, 250, [
    "SMOTENC lowered PR-AUC for both models it was tried on → class weighting kept",
    "After tuning (RandomizedSearchCV, PR-AUC), all three remain within one CV std → selection "
    "by documented rule: Recall@K, then **calibration error**, then fairness gap, then Brier, "
    "then fit time. **Chosen: random forest, all features**; isotonic calibration applied "
    "(ECE 0.054 → 0.017)",
    "Accuracy is reported but excluded from selection",
], size=15, gap=9)
source(s, "reports/tables/cv_comparison.csv · selection_matrix_ranked.csv · "
       "calibration_decision.json")

# ---- 08 Final held-out evaluation ---------------------------------------------------------
s = slide(prs)
eyebrow(s, "Final held-out evaluation", 8)
headline(s, "Evaluated once — `test_evaluations` = 1", size=29)
t = table(s, 72, 152, [268, 148, 148, 148, 154, 136, 134], [46, 44, 44])
for i, (h, al) in enumerate([("", PP_ALIGN.LEFT), ("PR-AUC", PP_ALIGN.RIGHT),
                             ("ROC-AUC", PP_ALIGN.RIGHT), ("Recall@K", PP_ALIGN.RIGHT),
                             ("Precision@K", PP_ALIGN.RIGHT), ("Brier", PP_ALIGN.RIGHT),
                             ("ECE", PP_ALIGN.RIGHT)]):
    head_cell(t, i, h, align=al)
for i, (name, vals, bg) in enumerate([
    ("**Final calibrated RF**", ("**0.817**", "0.892", "0.169", "0.96", "0.118", "0.034"),
     AMBER_L),
    ("Dummy baseline", ("0.321", "0.500", "0.074", "0.42", "0.218", "0.000"), PANEL),
], start=1):
    cell(t, i, 0, name, fill=bg)
    for j, v in enumerate(vals, start=1):
        cell(t, i, j, v, align=PP_ALIGN.RIGHT, fill=bg)
fw = figure(s, "reports/figures/test_pr_curve.png", 792, 300, 330)
bullets(s, 72, 306, 672, 330, [
    "Threshold 0.9728 = OOF score at the capacity selection rate (200 of 3539); on test it "
    "selects 57 students at precision 0.965",
    "**Recall@K is capacity-bound:** K = 50 slots for 284 eventual dropouts → ceiling ≈ 0.176; "
    "a 10-week window reaches 0.327",
    "Test PR-AUC matches the CV estimate (0.808): no sign of selection overfitting",
], size=15, gap=11)
source(s, "reports/tables/test_metrics_all_models.csv · threshold_and_bands.json · "
       "models/manifest.json")

# ---- 09 Explainability --------------------------------------------------------------------
s = slide(prs)
eyebrow(s, "Explainability", 9)
headline(s, "Named features, adviser-readable reasons", size=29)
fw = figure(s, "reports/explainability/shap_global_bar.png", 72, 160, 452)
bullets(s, 72 + fw + 48, 172, 1208 - (72 + fw + 48) - 72, 440, [
    "SHAP TreeExplainer on each of the 5 calibrated ensemble members, aggregated to source "
    "features, averaged; explains uncalibrated contributions",
    "Top drivers: `sem1_approval_rate`, Curricular units 1st sem (approved), Curricular units "
    "1st sem (grade), `grade_diff_vs_admission`, Application mode",
    "Local TP / FP / FN / TN cases rendered into supportive adviser phrases "
    "(`configs/language.yaml`); sensitive attributes can never appear as reasons (tested)",
    "PDP/ICE for 9 continuous raw features; engineered features explained via SHAP only",
], size=15, gap=12)
source(s, "reports/explainability/ · configs/language.yaml · tests/app/test_no_labels_rendered.py")

# ---- 10 Fairness audit --------------------------------------------------------------------
s = slide(prs)
eyebrow(s, "Fairness audit", 10)
headline(s, "Gender is near-equal; age is the material finding", size=30)
t = table(s, 72, 152, [446, 248, 158, 284], [48, 46, 46])
for i, (h, al) in enumerate([("Attribute", PP_ALIGN.LEFT),
                             ("Selection-rate gap (DP)", PP_ALIGN.RIGHT),
                             ("DI ratio", PP_ALIGN.RIGHT),
                             ("Equal-opportunity gap (TPR)", PP_ALIGN.RIGHT)]):
    head_cell(t, i, h, align=al)
cell(t, 1, 0, "Gender (female n=575, male n=310)", fill=WHITE)
for j, v in enumerate(("0.040", "0.56", "0.010"), start=1):
    cell(t, 1, j, v, align=PP_ALIGN.RIGHT, fill=WHITE)
cell(t, 2, 0, "Age band (4 bands, smallest n=85)", fill=AMBER_L)
for j, v in enumerate(("0.227", "0.08"), start=1):
    cell(t, 2, j, v, align=PP_ALIGN.RIGHT, fill=AMBER_L)
cell(t, 2, 3, "0.397", align=PP_ALIGN.RIGHT, fill=AMBER_L, color=RED, bold=True)
bullets(s, 72, 314, 1136, 330, [
    "Gender: list composition mirrors a two-fold base-rate difference; TPR nearly equal "
    "(0.189 vs 0.199); FPR < 1% both",
    "**Age: the material finding.** TPR 0.10 for 17–19 vs 0.50 for 35+: younger dropouts are "
    "under-reached through proxies (over-23 application route, programme, schedule)",
    "Mitigations on training OOF: reweighting (deployable; small parity gain, worse EO and "
    "calibration → not adopted); group thresholds (closes gender gap, needs gender at decision "
    "time → reported, not deployed)",
    "Recommended: adviser-side outreach-list allocation for younger bands; the Equity Dashboard "
    "shows the gap each cycle",
], size=15, gap=10)
source(s, "reports/fairness/group_metrics.csv · mitigation_comparison.csv · "
       "bias_fairness_analysis.md")

# ---- 11 Reproducibility -------------------------------------------------------------------
s = slide(prs)
eyebrow(s, "Reproducibility and engineering", 11)
headline(s, "Measured, not asserted — largest delta 0 on a fresh re-run")
bullets(s, 72, 168, 1136, 420, [
    "Single seed (42), config-driven CLI (`python -m ssn …`), pinned `requirements.txt`, "
    "`n_jobs=1` final fit",
    "Persisted pipeline + manifest: git SHA, config hash, pipeline SHA-256, library versions, "
    "exact 21-column input schema, threshold, bands, test counter",
    "**Fresh-environment re-run: maximum absolute delta 0** across every compared table "
    "(`docs/REPRODUCIBILITY.md`)",
    "**215 automated tests:** leakage (allow-list, fit isolation, parquet-read spies), privacy "
    "(no labels/sensitive columns in the demo cohort), metrics (hand-computed), artifact "
    "loading, language rules; CI on every push (lint, secrets scan, tests, language scan)",
], size=16, gap=14)
source(s, "docs/REPRODUCIBILITY.md · models/manifest.json · .github/workflows/ci.yml")

# ---- 12 Limitations -----------------------------------------------------------------------
s = slide(prs)
eyebrow(s, "Limitations", 12)
headline(s, "What this does not establish")
bullets(s, 72, 160, 1136, 450, [
    "**Scope:** one institution's history; no transfer to other institutions without "
    "re-training and re-auditing",
    "**Proxies:** parental qualification/occupation, application route, programme, schedule "
    "re-encode age and class",
    "**Leakage guard cost:** 3 excluded financial columns worth ≈ 0.037 PR-AUC; recording time "
    "still unverified (open item)",
    "**Uncertainty:** candidate differences are within CV noise; the choice rests on "
    "calibration and is documented as such",
    "**Not causal, not production-ready, not a replacement for advisers:** the tool proposes a "
    "short list; a qualified adviser decides, may override, and records the decision locally",
    "Full text: `reports/limitations.md`, `reports/bias_fairness_analysis.md`, "
    "`reports/model_card.md`",
], size=16, gap=12)
source(s, "reports/limitations.md · reports/bias_fairness_analysis.md · reports/model_card.md")

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(OUT)
print(f"wrote {OUT} — {len(prs.slides._sldIdLst)} slides, "
      f"{OUT.stat().st_size / 1024:.0f} KB")
