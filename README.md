# Student Success Navigator

[![CI](https://github.com/joopabs/student-success-navigator/actions/workflows/ci.yml/badge.svg)](https://github.com/joopabs/student-success-navigator/actions/workflows/ci.yml)

Fair and explainable first-semester dropout risk prediction for early academic support, with a
Dash decision-support companion app.

> **Status: Milestone 9 complete (Student Success Navigator Dash app).** Milestone 10 (MLOps/GenAI docs, demo media) remains.
> Metrics are measured; outreach capacity is an illustrative assumption. No production-readiness or causal claim is made.

## What this project does

A binary model estimates a **support-priority score** for each student at the end of their first
semester, using only information available at enrollment and during the first semester. Advisers
use the score to prioritise **voluntary, supportive outreach** within a limited weekly capacity.
The score is not a prediction about a student's worth or ability, it is not causal, and it is
never used to make or recommend adverse decisions.

**Explicit non-use.** This system must not be used to deny or restrict admission, enrollment,
scholarships, financial aid, grades, discipline, housing, or any student opportunity. All outreach
decisions require qualified human review.

**Data.** UCI Machine Learning Repository, *Predict Students' Dropout and Academic Success*
(CC BY 4.0). See [`data/README.md`](data/README.md) for citation, licence, and provenance. The data
comes from one higher-education institution and is not representative of Philippine institutions
or of universities generally.

## Rubric map

Each heading below corresponds to a criterion in the course rubric (`CAPSTONE_BRIEF.md`,
Section 5). Evidence links are filled in as milestones complete.

### Step 1: Problem understanding and framing (10 pts)
- Problem statement, task type, unit of analysis, prediction point: [`reports/final_report.md`](reports/final_report.md) section 1 · decisions in `PROJECT_DECISIONS.md`
- Primary metric PR-AUC; intervention metric Recall@K at an **illustrative** outreach capacity: `reports/tables/test_recall_precision_at_k.csv` (measured recall, illustrative K)

### Step 2: Data collection and understanding (10 pts)
- Source, licence, citation: [`data/README.md`](data/README.md)
- Dataset overview: [`reports/data_overview.md`](reports/data_overview.md) · Data dictionary: [`data/data_dictionary.md`](data/data_dictionary.md) · Profile tables: `reports/tables/profile_*.csv`

### Step 3: Data preprocessing, EDA, and feature engineering (10 pts)
- Cleaning, EDA, engineered features: [`reports/eda_feature_engineering_report.md`](reports/eda_feature_engineering_report.md) · figures in `reports/figures/` · notebook `notebooks/02_eda_feature_engineering.ipynb`
- Feature selection and PCA: [`reports/eda_feature_engineering_report.md`](reports/eda_feature_engineering_report.md) section 11 · `reports/tables/selection_*.csv`, `pca_*.csv` · `reports/figures/pca_*.png` · notebook `notebooks/03_feature_selection_pca.ipynb`

### Step 4: Model implementation and comparison (20 pts)
- Dummy baseline plus logistic regression, random forest, gradient boosting under CV: [`reports/model_comparison_cv.md`](reports/model_comparison_cv.md) · `reports/tables/cv_comparison.csv`, `ablation_*.csv` · `reports/figures/cv_pr_curves.png`, `cv_calibration.png` · notebook `notebooks/04_model_comparison.ipynb`
- Tuning, selection matrix, threshold, calibration, single held-out evaluation: [`reports/model_selection_and_evaluation.md`](reports/model_selection_and_evaluation.md) · `reports/tables/selection_matrix*.csv`, `threshold_and_bands.json`, `test_metrics*.csv`
- Saved pipeline and manifest: [`models/manifest.json`](models/manifest.json) (pipeline regenerated with `make final`; sha256 recorded)

### Step 5: Critical thinking, ethical AI, and bias auditing (20 pts)
- SHAP global/local, PDP/ICE: `reports/explainability/` (`shap_global_bar.png`, `shap_beeswarm.png`, `shap_local_examples.json`, `pdp_ice_*.png`, `method.json`) · notebook `notebooks/05_explainability_fairness.ipynb`
- Bias & Fairness Analysis: [`reports/bias_fairness_analysis.md`](reports/bias_fairness_analysis.md) · `reports/fairness/group_metrics.{csv,json}`, `attribute_summary.csv`, `mitigation_comparison.csv`, `selection_rates.png`, `group_calibration.png`
- Limitations and mitigations: [`reports/limitations.md`](reports/limitations.md) · Model card: [`reports/model_card.md`](reports/model_card.md)

### Step 6: Final presentation and communication (10 pts)
- Technical deck (12 slides): [`reports/decks/technical_deck.slides.html`](reports/decks/technical_deck.slides.html) built from `notebooks/90_technical_deck.ipynb`
- Business deck (10 slides): outline with figure paths and guardrails in [`reports/decks/business_deck_outline.md`](reports/decks/business_deck_outline.md); assembled file `reports/decks/business_deck.pptx` (assembly checklist in the outline)

### Step 7: GitHub profile and upload (15 pts)
- Repository structure: see below. Final report: [`reports/final_report.md`](reports/final_report.md) (HTML export `reports/final_report.html`) · Rubric evidence map: [`reports/rubric_map.md`](reports/rubric_map.md)

### Bonus: creative and well-presented submission (5 pts)
- Student Success Navigator Dash app (optional Step 8): `python -m ssn app` · guide [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) · six pages (Overview, Support Queue, Student Review, New Record Scoring, Equity Dashboard, Model Card) · loads the saved pipeline, never retrains · acknowledgement-gated local action log · 30 app tests under `tests/app/`
- MLOps and Generative AI documentation (optional Steps 8-9): planned in Milestone 10 (`docs/MLOPS.md`, `docs/GENAI_USE.md` when written)

## Reproduction

Requires Python 3.11.

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest -q          # Milestone 1 smoke tests
python -m ssn --version
```

End-to-end reproduction from the raw download to the audited model (about 8 minutes on a laptop):

```bash
make data      # download (checksum-verified), validate, profile, clean, split
make eda       # EDA figures and tables (training split)
make select    # feature selection + PCA under CV
make cv        # dummy + candidates under CV
make tune      # RandomizedSearchCV
make final     # select-model, calibrate, threshold, fit-final, evaluate-test (the single held-out pass)
make explain   # SHAP, PDP/ICE
make fairness  # group audit + mitigation experiment
make report    # model card, rubric map, language scan
make app       # Student Success Navigator at http://127.0.0.1:8050 (python -m ssn app)
```

A second run in a fresh environment reproduced every compared table with a maximum absolute delta of 0
(`docs/REPRODUCIBILITY.md`). Tests: `make test`; lint: `make lint`; secrets scan: `make secrets`.

## Repository structure

```text
configs/        base.yaml (seed, paths, illustrative capacity, fairness settings); model configs
data/           README.md; raw/ interim/ processed/ demo/ evaluation/ local/ (contents Git-ignored)
docs/           deployment, MLOps, GenAI, reproducibility notes
models/         final pipeline (Git-ignored) and manifest.json (committed)
notebooks/      profiling, EDA, selection/PCA, model comparison, explainability/fairness, deck
reports/        final report, model card, rubric map; figures/ tables/ explainability/ fairness/ decks/
src/ssn/        data/ features/ modeling/ explain/ fairness/ reporting/ app/
tests/          unit/ integration/ app/
specs/          Spec Kit artifacts: spec, plan, research, data model, contracts, tasks
```

## Governance

Project rules live in `.specify/memory/constitution.md`. Key commitments: leakage-safe features
(enrollment and first semester only), sensitive attributes used for aggregate fairness auditing
and never as model inputs, single held-out test evaluation, fixed seeds and config-driven runs, and
a human-in-the-loop app that never displays outcomes or identifiers.

## Licence

Code, notebooks, and reports: [MIT](LICENSE). Dataset: CC BY 4.0, attributed in `data/README.md`.
