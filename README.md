# Student Success Navigator

Fair and explainable first-semester dropout risk prediction for early academic support, with a
Dash decision-support companion app.

> **Status: Milestone 2 complete (data acquisition, schema validation, profiling, data dictionary).**
> No model has been trained and no model results exist yet. Every `[PENDING: ...]` marker below names the artifact that will supply
> the value once the pipeline has actually been run.

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
- Problem statement, task type, unit of analysis, prediction point: `[PENDING: reports/final_report.md]`
- Primary metric PR-AUC; intervention metric Recall@K at an **illustrative** outreach capacity: `[PENDING: reports/tables/test_recall_precision_at_k.csv]`

### Step 2: Data collection and understanding (10 pts)
- Source, licence, citation: [`data/README.md`](data/README.md)
- Dataset overview: [`reports/data_overview.md`](reports/data_overview.md) · Data dictionary: [`data/data_dictionary.md`](data/data_dictionary.md) · Profile tables: `reports/tables/profile_*.csv`

### Step 3: Data preprocessing, EDA, and feature engineering (10 pts)
- Cleaning before/after counts, EDA, engineered features, selection, PCA: `[PENDING: reports/eda_feature_engineering_report.md]`

### Step 4: Model implementation and comparison (20 pts)
- Dummy baseline plus logistic regression, random forest, gradient boosting: `[PENDING: reports/tables/cv_comparison.csv]`
- Selection matrix and final test evaluation: `[PENDING: reports/tables/selection_matrix.csv, reports/tables/test_metrics.csv]`
- Saved pipeline and manifest: `[PENDING: models/manifest.json]`

### Step 5: Critical thinking, ethical AI, and bias auditing (20 pts)
- SHAP, PDP/ICE: `[PENDING: reports/explainability/]`
- Bias & Fairness Analysis by verified gender encoding and age bands: `[PENDING: reports/fairness/group_metrics.csv]`
- Limitations and mitigations: `[PENDING: reports/limitations.md]`

### Step 6: Final presentation and communication (10 pts)
- Technical deck (8-12 slides): `[PENDING: reports/decks/technical_deck.slides.html]`
- Business deck (8-12 slides): `[PENDING: reports/decks/business_deck.pptx]`

### Step 7: GitHub profile and upload (15 pts)
- Repository structure: see below. Final report: `[PENDING: reports/final_report.md]`

### Bonus: creative and well-presented submission (5 pts)
- Student Success Navigator Dash app (optional Step 8): `[PENDING: docs/DEPLOYMENT.md]`
- MLOps and Generative AI documentation (optional Steps 8-9): `[PENDING: docs/MLOPS.md, docs/GENAI_USE.md]`

## Reproduction

Requires Python 3.11.

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest -q          # Milestone 1 smoke tests
python -m ssn --version
```

End-to-end reproduction (download, clean, split, train, evaluate, explain, audit) is wired in
later milestones: `[PENDING: Makefile targets per specs/001-dropout-risk-navigator/contracts/cli.md]`.
Reproduction tolerance: `[PENDING: docs/REPRODUCIBILITY.md]`.

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
