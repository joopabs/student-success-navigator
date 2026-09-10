"""Render reports/rubric_map.md: one row per rubric criterion with evidence links (T069).

Criteria and points come from CAPSTONE_BRIEF.md section 5. Evidence cells are regenerated from the
EVIDENCE table below; a hand-written notes block survives regeneration.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

NOTES_START, NOTES_END = "<!-- BEGIN NOTES -->", "<!-- END NOTES -->"

CRITERIA: list[tuple[str, int, list[str]]] = [
    (
        "1: Problem Understanding & Framing",
        10,
        [
            "reports/final_report.md#1-problem-understanding-and-framing",
            "PROJECT_DECISIONS.md",
            "reports/tables/test_recall_precision_at_k.csv",
            "configs/base.yaml",
        ],
    ),
    (
        "Step 2: Data Collection & Understanding",
        10,
        [
            "data/README.md",
            "reports/data_overview.md",
            "data/data_dictionary.md",
            "reports/tables/profile_columns.csv",
            "reports/tables/profile_target.csv",
            "notebooks/01_data_profiling.ipynb",
        ],
    ),
    (
        "Step 3: Data Preprocessing, EDA & Feature Engineering",
        10,
        [
            "reports/eda_feature_engineering_report.md",
            "reports/tables/clean_before_after.csv",
            "reports/figures/eda_correlation_spearman.png",
            "reports/tables/selection_decision.json",
            "reports/tables/pca_vs_nopca_cv.csv",
            "src/ssn/features/engineering.py",
            "notebooks/02_eda_feature_engineering.ipynb",
            "notebooks/03_feature_selection_pca.ipynb",
        ],
    ),
    (
        "Step 4: Model Implementation & Comparison",
        20,
        [
            "reports/model_comparison_cv.md",
            "reports/model_selection_and_evaluation.md",
            "reports/tables/cv_comparison.csv",
            "reports/tables/selection_matrix_ranked.csv",
            "reports/tables/test_metrics_all_models.csv",
            "models/manifest.json",
            "docs/REPRODUCIBILITY.md",
            "notebooks/04_model_comparison.ipynb",
        ],
    ),
    (
        "Step 5: Critical Thinking, Ethical AI & Bias Auditing",
        20,
        [
            "reports/bias_fairness_analysis.md",
            "reports/limitations.md",
            "reports/model_card.md",
            "reports/explainability/shap_global_bar.png",
            "reports/explainability/shap_local_examples.json",
            "reports/fairness/group_metrics.csv",
            "reports/fairness/mitigation_comparison.csv",
            "notebooks/05_explainability_fairness.ipynb",
        ],
    ),
    (
        "Step 6: Final Presentation & Communication",
        10,
        [
            "reports/decks/technical_deck.slides.html",
            "notebooks/90_technical_deck.ipynb",
            "reports/decks/business_deck_outline.md",
            "reports/decks/business_deck.pptx",
        ],
    ),
    (
        "Step 7: GitHub Profile & Upload",
        15,
        [
            "README.md",
            "requirements.txt",
            "reports/final_report.md",
            "tests",
            ".github/workflows/ci.yml",
            "LICENSE",
        ],
    ),
    (
        "Bonus: Creative and well-presented submission",
        5,
        [
            "docs/DEPLOYMENT.md",
            "docs/MLOPS.md",
            "docs/GENAI_USE.md",
            "src/ssn/app",
            "reports/decks/demo.gif",
        ],
    ),
]


def _existing_notes(path: Path) -> str:
    if path.is_file():
        m = re.search(
            re.escape(NOTES_START) + r".*?" + re.escape(NOTES_END), path.read_text(), re.S
        )
        if m:
            return m.group(0)
    return f"{NOTES_START}\n_Hand-written notes (e.g. submission checklist completion) go here and survive regeneration._\n{NOTES_END}"


def render(root: Path, out_path: Path) -> tuple[str, list[str]]:
    rows, missing = [], []
    total = 0
    for name, pts, evidence in CRITERIA:
        total += pts
        links = []
        for e in evidence:
            target = e.split("#")[0]
            exists = (root / target).exists()
            if not exists:
                missing.append(e)
            links.append(f"[`{e}`](../{e})" + ("" if exists else " (pending)"))
        rows.append(f"| {name} | {pts} | " + "<br>".join(links) + " |")
    text = "\n".join(
        [
            "# Rubric Evidence Map",
            "",
            f"**Generated:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')} by `python -m ssn rubric-map`. Criteria and points from",
            "`CAPSTONE_BRIEF.md` section 5 (total 100, bonus included). Links are relative to `reports/`; an item marked",
            "(pending) does not exist yet in the repository.",
            "",
            "| Criterion | Points | Evidence |",
            "|---|---|---|",
            *rows,
            f"| **Total** | **{total}** | |",
            "",
            _existing_notes(out_path),
            "",
        ]
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text)
    return text, missing
