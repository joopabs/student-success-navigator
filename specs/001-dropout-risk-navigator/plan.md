# Implementation Plan: Fair and Explainable Student Dropout Risk Prediction for Early Academic Support

**Branch**: `001-dropout-risk-navigator` | **Date**: 2026-09-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-dropout-risk-navigator/spec.md`

**Governing documents**: `CAPSTONE_BRIEF.md`, `PROJECT_DECISIONS.md`,
`.specify/memory/constitution.md` v1.0.0.

## Summary

Build a reproducible, leakage-safe binary classifier that estimates a first-semester dropout
support-priority score from the UCI "Predict Students' Dropout and Academic Success" dataset, using
only enrollment-time and first-semester features. Compare a dummy baseline against class-weighted
logistic regression, random forest, and gradient boosting under stratified cross-validation, select
on PR-AUC, Recall@K/Precision@K at an illustrative outreach capacity, calibration, fairness,
explainability, and maintainability, then evaluate once on a held-out test set. Explain the model
with SHAP and PDP/ICE, audit fairness by verified gender encoding and age bands, and ship a final
report, two 8-12 slide decks, and a Dash decision-support app (Student Success Navigator) that
loads the saved pipeline without retraining and serves a de-identified demo cohort whose true
outcomes live only in an evaluator-only dataset.

Technical approach: a single Python 3.11 package (`src/ssn/`) exposing a config-driven CLI
(`python -m ssn <command>`) that produces every artifact deterministically from `configs/*.yaml`;
scikit-learn `Pipeline`/`ColumnTransformer` so all fitting happens inside folds; joblib artifacts
with a JSON manifest; pytest for leakage, privacy, and logic tests; Dash Pages for the app.

## Technical Context

**Language/Version**: Python 3.11 (pinned in `.python-version` and `pyproject.toml`)

**Primary Dependencies**: pandas, numpy, scikit-learn, imbalanced-learn (imbalance experiment
only), shap, matplotlib, seaborn, joblib, PyYAML (config), pyarrow (parquet), Dash, Plotly. Dev:
pytest, pytest-cov, ruff, nbconvert (technical deck). Optional: xgboost (only if
HistGradientBoosting proves inadequate; see research R-06), python-pptx (not planned; business
deck authored in PowerPoint/Canva from exported figures).

**Storage**: Files only. Raw CSV under `data/raw/` (Git-ignored, downloaded by script with
checksum). Processed parquet under `data/processed/`, demo cohort under `data/demo/`,
evaluator-only labels under `data/evaluation/` (all Git-ignored, regenerable). Model artifacts
under `models/`. SQLite action log at `data/local/actions.sqlite` (Git-ignored).

**Testing**: pytest with unit tests (`tests/unit`), integration tests running the pipeline on a
small deterministic fixture (`tests/integration`), and app tests using Dash's testing helpers or
direct layout/callback invocation (`tests/app`).

**Target Platform**: Local macOS/Linux workstation; CI on GitHub Actions ubuntu-latest (optional
M10). Dash served on localhost only.

**Project Type**: Single Python project: data-science pipeline package plus a Dash web app that
consumes its artifacts.

**Performance Goals**: Full pipeline (data through evaluation and explainability) completes in
under 30 minutes on a laptop CPU; app cold start scores the demo cohort in under 30 seconds; page
interactions respond in under 2 seconds.

**Constraints**: No retraining inside the app. No network calls from the app. No student
identifiers or outcome labels in adviser-facing pages. Deterministic outputs given seed and config.
No secrets in repo. Course PDF remains Git-ignored.

**Capacity framing**: K = illustrative students per week times an illustrative outreach window
(default 10 x 5 weeks = 50); sensitivity over alternative windows. See research R-08.

**Scale/Scope**: 4,424 records and 36 features per UCI page (to be re-verified by PV-01). Roughly
80/20 split yields a test/demo cohort in the high hundreds. Six app pages. One model in
production at a time.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Gate | How this plan satisfies it | Status |
|------------------|----------------------------|--------|
| I Assignment fidelity (G10) | Milestones M1-M10 map to capstone Steps 1-9; rubric map produced in M8 | PASS |
| II Business framing (G1) | M1 config carries `capacity_k` and `illustrative: true` flags; M8 report states problem, unit, prediction point, metrics | PASS |
| III Provenance & privacy (G2) | M2 records CC BY 4.0 licence, DOI, citation, checksum; raw/processed/demo/evaluation data and action log Git-ignored; secrets scan in M1 | PASS |
| IV Reproducibility (G9) | Single seed in `configs/base.yaml`; CLI-only runs; manifest with config hash and git SHA; reproduction test in M6 | PASS |
| V Leakage-safe features (G3) | `configs/features.yaml` classifies every column; `tests/unit/test_allowlist.py` fails on prohibited or unclassified columns; all transformers inside sklearn Pipeline | PASS |
| VI Data quality (G4) | M2 profiling and M3 cleaning emit before/after count tables from code | PASS |
| VII EDA/FE/selection/PCA (G4) | M3 and M4 implement filter + embedded selection and PCA inside folds | PASS |
| VIII Baseline + multi-criteria selection (G5) | M5 compares Dummy + LR + RF + HGB; M6 selection matrix across all criteria; accuracy not a selection input | PASS |
| IX Explainability (G6) | M7 SHAP global/local, PDP/ICE, neutral-language mapping | PASS |
| X Fairness audit (G7) | M7 group metrics with n, min-group warnings, mitigation experiment, residual risk | PASS |
| XI Human-in-the-loop (G8) | M9 app: no identifiers, no outcomes, acknowledgement gate, append-only log, version check, disclaimer | PASS |
| XII Communication & repo (G10) | M1 scaffold matches required structure; M8 decks and report | PASS |
| Stack constraint | All libraries within constitution stack; PyYAML and pyarrow added as minimal utilities (justified in research R-02) | PASS |

No violations. Complexity Tracking is therefore empty.

**Post-design re-check (after Phase 1)**: data-model.md separates `DemoCohort` from
`EvaluatorLabels`; contracts/app-pages.md lists forbidden fields per page; contracts/cli.md
shows no command that both writes adviser-facing data and reads labels. Gates remain PASS.

## Project Structure

### Documentation (this feature)

```text
specs/001-dropout-risk-navigator/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── config-schema.md
│   ├── feature-allowlist.md
│   ├── cli.md
│   ├── artifact-manifest.md
│   ├── app-pages.md
│   └── action-log.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks - NOT created here)
```

### Source Code (repository root)

```text
.
├── README.md
├── requirements.txt              # pinned runtime deps
├── requirements-dev.txt          # pytest, ruff, nbconvert
├── pyproject.toml                # package metadata, ruff + pytest config
├── Makefile                      # thin wrappers over `python -m ssn ...`
├── .python-version               # 3.11
├── .gitignore
├── .env.example
├── CAPSTONE_BRIEF.md
├── PROJECT_DECISIONS.md
├── configs/
│   ├── base.yaml                 # seed, paths, split, capacity_k, bands, min_group_size
│   ├── features.yaml             # column availability classification + allow-list
│   ├── language.yaml             # neutral phrase per feature; prohibited terms
│   └── models/
│       ├── dummy.yaml
│       ├── logreg.yaml
│       ├── random_forest.yaml
│       └── hist_gb.yaml
├── data/
│   ├── README.md                 # source, citation, licence, checksum, download steps
│   ├── data_dictionary.md        # generated + hand-annotated
│   ├── raw/                      # .gitkeep only; data.csv Git-ignored
│   ├── processed/                # Git-ignored, regenerable
│   ├── demo/                     # Git-ignored: demo_cohort.parquet (no labels)
│   ├── evaluation/               # Git-ignored: demo_cohort_labels.parquet (evaluator-only)
│   └── local/                    # Git-ignored: actions.sqlite
├── src/ssn/
│   ├── __init__.py
│   ├── __main__.py               # `python -m ssn`
│   ├── cli.py                    # argparse subcommands
│   ├── config.py                 # load/validate YAML, seed propagation
│   ├── paths.py
│   ├── data/
│   │   ├── download.py           # fetch UCI zip/csv, verify sha256
│   │   ├── schema.py             # expected columns, dtypes, ranges (from PV tasks)
│   │   ├── profile.py            # missingness, duplicates, ranges, outliers -> tables
│   │   ├── clean.py
│   │   └── split.py              # stratified train/test, synthetic IDs, demo/eval split
│   ├── features/
│   │   ├── allowlist.py          # load features.yaml, enforce, raise on unclassified
│   │   ├── engineering.py        # rate features, grade diff, age band (sklearn transformer)
│   │   └── preprocess.py         # ColumnTransformer builder
│   ├── modeling/
│   │   ├── candidates.py         # build pipelines from configs/models/*.yaml
│   │   ├── selection.py          # filter + embedded selectors as pipeline steps
│   │   ├── pca.py                # PCA experiment + 2D projection
│   │   ├── cv.py                 # StratifiedKFold, OOF predictions
│   │   ├── tune.py               # RandomizedSearchCV per candidate
│   │   ├── threshold.py          # capacity-aware threshold + bands from OOF scores
│   │   ├── evaluate.py           # metrics, Recall@K, Precision@K, calibration
│   │   ├── calibrate.py          # CalibratedClassifierCV comparison
│   │   └── persist.py            # joblib + manifest.json
│   ├── explain/
│   │   ├── shap_explain.py
│   │   ├── pdp_ice.py
│   │   └── language.py           # feature -> neutral phrase; prohibited-term scan
│   ├── fairness/
│   │   ├── groups.py             # gender (verified encoding), age bands
│   │   ├── metrics.py            # selection rate, DPD, DIR, TPR, FPR, EOD, calibration
│   │   ├── audit.py              # per-group tables with n and warnings
│   │   └── mitigate.py           # reweighting / per-group threshold experiment
│   ├── reporting/
│   │   ├── figures.py
│   │   ├── tables.py
│   │   ├── model_card.py         # renders reports/model_card.md from manifest + results
│   │   └── rubric_map.py
│   └── app/
│       ├── __init__.py
│       ├── app.py                # Dash app factory, loads pipeline + manifest, version check
│       ├── services/
│       │   ├── scoring.py        # predict_proba on demo cohort / hypothetical record
│       │   ├── explanations.py   # local SHAP -> neutral phrases
│       │   ├── actions.py        # SQLite append-only log
│       │   └── equity.py         # reads reports/fairness/*.json only
│       ├── components/
│       │   ├── disclaimer.py
│       │   └── record_card.py
│       └── pages/
│           ├── overview.py
│           ├── support_queue.py
│           ├── student_review.py
│           ├── new_record.py
│           ├── equity_dashboard.py
│           └── model_card.py
├── notebooks/
│   ├── 01_data_profiling.ipynb
│   ├── 02_eda_feature_engineering.ipynb
│   ├── 03_feature_selection_pca.ipynb
│   ├── 04_model_comparison.ipynb
│   ├── 05_explainability_fairness.ipynb
│   └── 90_technical_deck.ipynb   # nbconvert --to slides
├── models/
│   ├── .gitkeep
│   ├── final_pipeline.joblib     # Git-ignored; regenerate with `make final`; sha256 in manifest
│   └── manifest.json
├── reports/
│   ├── final_report.md
│   ├── eda_feature_engineering_report.md
│   ├── model_card.md
│   ├── rubric_map.md
│   ├── figures/
│   ├── tables/
│   ├── explainability/
│   ├── fairness/
│   └── decks/
│       ├── technical_deck.slides.html
│       ├── business_deck.pptx
│       └── business_deck_outline.md
├── docs/
│   ├── DEPLOYMENT.md
│   ├── MLOPS.md
│   ├── GENAI_USE.md
│   └── REPRODUCIBILITY.md
├── tests/
│   ├── conftest.py               # tiny deterministic fixture frame (synthetic, not real rows)
│   ├── unit/
│   ├── integration/
│   └── app/
└── .github/workflows/ci.yml      # optional M10: ruff + pytest
```

**Structure Decision**: Single project. The Dash app lives inside the same package
(`src/ssn/app/`) so it imports the exact feature-engineering and language code used in training,
avoiding drift. Data directories are split by audience: `data/demo/` (adviser-facing, no labels)
versus `data/evaluation/` (evaluator-only labels). The app package is forbidden by test from
importing `ssn.fairness.audit`, `ssn.modeling.evaluate`, or reading `data/evaluation/`.

## Complexity Tracking

No constitution violations; nothing to justify.

## Implementation Milestones

Conventions used below:

- **Computed, not narrated** lists items whose values MUST come from code output (tables, JSON,
  figures) and be pasted or linked into reports. Writing these as prose without a generating
  artifact is a defect.
- **Verification** commands assume an activated virtual environment at repo root.
- Every milestone ends with `ruff check . && pytest -q` passing.

### M1. Repository scaffold, quality tooling, configuration, and test foundations

**Creates/modifies**: `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`,
`.python-version`, `Makefile`, `.env.example`, `.gitignore` (add `data/raw/*`,
`data/processed/`, `data/demo/`, `data/evaluation/`, `data/local/`, `models/*.joblib`; figures
under `reports/` are committed per R-11), `README.md` (skeleton with rubric-mapped sections),
`configs/base.yaml`, `configs/features.yaml` (skeleton, all columns `unclassified` until M2),
`configs/language.yaml`, `configs/models/*.yaml`, `src/ssn/{__init__,__main__,cli,config,paths}.py`,
`src/ssn/features/allowlist.py`, `tests/conftest.py`, `tests/unit/test_config.py`,
`tests/unit/test_allowlist.py`, `tests/unit/test_language.py`, all package `__init__.py` files,
`data/README.md` (placeholder), `.gitkeep` files.

**Inputs**: spec, constitution, contracts/config-schema.md, contracts/feature-allowlist.md.

**Outputs**: importable `ssn` package; `python -m ssn --help` lists subcommands; config loader
validates against schema and exposes a single `seed`.

**Dependencies**: none (first milestone).

**Tests / verification**:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
ruff check . && pytest -q
python -m ssn --help
python -m ssn config validate --config configs/base.yaml
git ls-files | grep -Ei 'data/raw/.*csv|\.env$|\.sqlite' && echo "LEAK" || echo "clean"
```

**Privacy / leakage checks**: `.gitignore` covers raw, processed, demo, evaluation, local data,
`.env`, SQLite; `tests/unit/test_allowlist.py` asserts that an unclassified column raises;
`tests/unit/test_language.py` asserts prohibited terms list is loaded and the scanner flags them.

**Acceptance criteria**: All commands above succeed; `configs/features.yaml` loads with zero
allowed columns (nothing is allowed until classified in M2); README skeleton has headings for
every rubric criterion.

**Computed, not narrated**: none yet (scaffold only).

### M2. UCI dataset acquisition documentation, schema validation, profiling, and data dictionary

**Creates/modifies**: `src/ssn/data/download.py`, `src/ssn/data/schema.py`,
`src/ssn/data/profile.py`, `configs/features.yaml` (fill classification for every column),
`data/README.md` (citation, DOI 10.24432/C5MC89, CC BY 4.0, access date, sha256, download steps),
`data/data_dictionary.md`, `reports/tables/profile_*.csv`, `notebooks/01_data_profiling.ipynb`,
`tests/unit/test_schema.py`, `tests/unit/test_features_yaml_complete.py`,
`tests/integration/test_profile_fixture.py`.

**Inputs**: UCI dataset 697 CSV; UCI variables table and the source publication for encodings.

**Outputs**: `data/raw/data.csv` (local), `reports/tables/profile_columns.csv` (name, dtype,
n_missing, n_unique, min, max, availability class), `reports/tables/profile_target.csv` (class
counts and `is_dropout` balance), `reports/tables/profile_duplicates.csv`,
`data/data_dictionary.md` (generated table + hand-written encoding notes with verification status
per column).

**Dependencies**: M1.

**Tests / verification**:

```bash
python -m ssn data download --config configs/base.yaml      # verifies sha256 recorded in data/README.md
python -m ssn data validate --config configs/base.yaml      # schema: expected columns, dtypes, Target values
python -m ssn data profile --config configs/base.yaml       # writes reports/tables/profile_*.csv
pytest -q tests/unit/test_schema.py tests/unit/test_features_yaml_complete.py
```

**Privacy / leakage checks**: `test_features_yaml_complete.py` asserts every raw column has
exactly one availability class in {enrollment, first_semester, second_semester, outcome,
ambiguous} and that `second_semester`, `outcome`, and `ambiguous` are excluded from the allow-list
by default (R-05). `data validate` fails if `Target` contains values other than the three
expected classes. No raw rows are printed into notebooks committed to Git beyond `head()` of
de-identified columns.

**Acceptance criteria**: PV-01, PV-02, PV-03, PV-04 (encoding sources recorded, verified or
marked unverified per column), PV-05, PV-09 recorded in `data/README.md` and
`data/data_dictionary.md`; every column classified; licence text present; checksum matches.

**Computed, not narrated**: record and column counts; `Target` frequencies and derived
`is_dropout` balance; per-column missing, unique, min, max; duplicate count; observed category
values per categorical column (to compare with documented encodings).

### M3. Cleaning, EDA, leakage-safe feature engineering, and visual reporting

**Creates/modifies**: `src/ssn/data/clean.py`, `src/ssn/data/split.py`,
`src/ssn/features/engineering.py`, `src/ssn/features/preprocess.py`,
`src/ssn/reporting/figures.py`, `notebooks/02_eda_feature_engineering.ipynb`,
`reports/eda_feature_engineering_report.md`, `reports/figures/eda_*.png`,
`reports/tables/clean_before_after.csv`, `tests/unit/test_clean.py`,
`tests/unit/test_engineering.py`, `tests/unit/test_split.py`.

**Inputs**: `data/raw/data.csv`, `configs/features.yaml`, `configs/base.yaml`.

**Outputs**: `data/processed/train.parquet`, `data/processed/test.parquet` (both with
`record_id` synthetic key and `is_dropout`), `data/demo/demo_cohort.parquet` (test features only,
no `Target`, no `is_dropout`), `data/evaluation/demo_cohort_labels.parquet` (`record_id`,
`is_dropout`, `Target`), EDA figures, before/after cleaning table, EDA report.

**Dependencies**: M2 (classification complete).

**Tests / verification**:

```bash
python -m ssn data clean --config configs/base.yaml
python -m ssn data split --config configs/base.yaml
python -m ssn eda --config configs/base.yaml
pytest -q tests/unit/test_clean.py tests/unit/test_engineering.py tests/unit/test_split.py
python - <<'PY'
import pandas as pd
d = pd.read_parquet('data/demo/demo_cohort.parquet')
assert not {'Target','is_dropout'} & set(d.columns), "labels leaked into demo cohort"
print("demo cohort clean:", d.shape)
PY
```

**Privacy / leakage checks**: `test_split.py` asserts demo cohort has no label columns and that
`record_id` is a random synthetic key (not row index); asserts train/test disjoint by
`record_id`; `test_engineering.py` asserts every engineered feature's inputs are in the
allow-list (introspects transformer's declared inputs) and that zero denominators are handled
per documented rule (FR-028). EDA of second-semester columns, if any, is in a clearly titled
"analysis-only" notebook section and writes to `reports/figures/analysis_only_*.png`.

**Acceptance criteria**: Before/after counts for missing, duplicates, invalid, outliers exist in
`clean_before_after.csv`; class balance of train and test reported; engineered features listed
with one-line rationale in the EDA report; figures saved; all tests pass.

**Computed, not narrated**: all before/after counts; train/test sizes and positive rates;
distributions, correlations, target relationships; zero-denominator counts for rate features;
age distribution summary feeding PV-06.

### M4. Train-only feature selection and PCA analysis

**Creates/modifies**: `src/ssn/modeling/selection.py`, `src/ssn/modeling/pca.py`,
`src/ssn/modeling/cv.py`, `notebooks/03_feature_selection_pca.ipynb`,
`reports/tables/selection_filter_scores.csv`, `reports/tables/selection_embedded_scores.csv`,
`reports/tables/pca_explained_variance.csv`, `reports/tables/pca_vs_nopca_cv.csv`,
`reports/figures/pca_scree.png`, `reports/figures/pca_2d_train.png`,
`tests/unit/test_selection_in_pipeline.py`, `tests/unit/test_pca_fit_isolation.py`.

**Inputs**: `data/processed/train.parquet` only.

**Outputs**: selector configuration (chosen k or threshold) written to
`reports/tables/selection_decision.json`; PCA comparison table; figures.

**Dependencies**: M3.

**Tests / verification**:

```bash
python -m ssn select --config configs/base.yaml
python -m ssn pca --config configs/base.yaml
pytest -q tests/unit/test_selection_in_pipeline.py tests/unit/test_pca_fit_isolation.py
```

**Privacy / leakage checks**: `test_pca_fit_isolation.py` fits the pipeline on a fixture train
split and asserts the PCA/selector components are unchanged by the presence of test rows (fit
only inside `Pipeline` within `cross_validate`). No test-set rows are read by `select` or `pca`
commands (paths asserted in test via a spy on `read_parquet`).

**Acceptance criteria**: One filter method (mutual information or ANOVA F) and one embedded
method (L1 logistic or tree importances) run inside CV; selection decision justified in notebook
and EDA report; PCA explained-variance curve and CV comparison against non-PCA pipeline saved.

**Computed, not narrated**: filter scores, embedded importances, chosen feature subset, PCA
explained-variance ratios, CV PR-AUC with and without PCA.

### M5. Dummy baseline and multi-model validation comparison

**Creates/modifies**: `src/ssn/modeling/candidates.py`, `src/ssn/modeling/evaluate.py`
(metric functions incl. Recall@K, Precision@K), `configs/models/*.yaml`,
`notebooks/04_model_comparison.ipynb`, `reports/tables/cv_comparison.csv`,
`reports/figures/cv_pr_curves.png`, `tests/unit/test_metrics.py`,
`tests/unit/test_candidates_build.py`, `tests/integration/test_cv_fixture.py`.

**Inputs**: `data/processed/train.parquet`, selection decision from M4.

**Outputs**: `reports/tables/cv_comparison.csv` with per-model mean and std for PR-AUC, ROC-AUC,
recall, precision, F1, Recall@K, Precision@K (K scaled to fold size per R-08), Brier score; OOF
predictions per model saved to `data/processed/oof_<model>.parquet` for M6 threshold selection.

**Dependencies**: M4.

**Tests / verification**:

```bash
python -m ssn train-cv --config configs/base.yaml --models dummy logreg random_forest hist_gb
pytest -q tests/unit/test_metrics.py tests/integration/test_cv_fixture.py
```

**Privacy / leakage checks**: `train-cv` reads only train parquet (asserted); imbalanced-learn
resampling, if compared, occurs inside `imblearn.pipeline.Pipeline` so it touches training folds
only (`test_cv_fixture.py` asserts validation fold sizes unchanged).

**Acceptance criteria**: Dummy plus at least three non-trivial models in the table; every
metric reported with std; accuracy present in the table for transparency but excluded from the
selection matrix; class-weighting versus resampling comparison recorded.

**Computed, not narrated**: every value in `cv_comparison.csv`; PR curves.

### M6. Tuning, capacity-aware thresholding, held-out test evaluation, calibration, and saved pipeline/artifacts

**Creates/modifies**: `src/ssn/modeling/tune.py`, `src/ssn/modeling/threshold.py`,
`src/ssn/modeling/calibrate.py`, `src/ssn/modeling/persist.py`,
`reports/tables/tuning_results_<model>.csv`, `reports/tables/selection_matrix.csv`,
`reports/tables/threshold_and_bands.json`, `reports/tables/test_metrics.csv`,
`reports/tables/test_recall_precision_at_k.csv` (K sensitivity), `reports/figures/test_pr_curve.png`,
`reports/figures/test_calibration.png`, `reports/figures/test_confusion_matrix.png`,
`models/final_pipeline.joblib`, `models/manifest.json`, `docs/REPRODUCIBILITY.md`,
`tests/unit/test_threshold.py`, `tests/unit/test_persist_manifest.py`,
`tests/integration/test_reproduce_fixture.py`.

**Inputs**: train parquet, OOF predictions, test parquet (read exactly once by `evaluate-test`).

**Outputs**: tuned candidates; selection matrix across PR-AUC, Recall@K, Precision@K,
calibration (Brier, ECE), fairness summary (from a CV-based preliminary audit), explainability
feasibility, maintainability notes; chosen threshold and band boundaries; single test evaluation;
persisted pipeline and manifest (see contracts/artifact-manifest.md).

**Dependencies**: M5 (and a preliminary run of M7 fairness metrics on OOF predictions for the
selection matrix; implemented as `ssn.fairness.metrics` used by `select-model`).

**Tests / verification**:

```bash
python -m ssn tune --config configs/base.yaml --models logreg random_forest hist_gb
python -m ssn select-model --config configs/base.yaml          # writes selection_matrix.csv + decision
python -m ssn threshold --config configs/base.yaml             # OOF-based, capacity-aware
python -m ssn calibrate --config configs/base.yaml
python -m ssn fit-final --config configs/base.yaml             # refit on full train, persist
python -m ssn evaluate-test --config configs/base.yaml         # ONE run; writes test_* artifacts
pytest -q tests/unit/test_threshold.py tests/unit/test_persist_manifest.py tests/integration/test_reproduce_fixture.py
# reproduction check (second fresh run, compare)
python -m ssn reproduce-check --runs-a reports --runs-b /tmp/ssn-run2/reports
```

**Privacy / leakage checks**: `evaluate-test` is the only command permitted to read
`data/processed/test.parquet` labels; the CLI records in the manifest the number of times test
evaluation has been run (`test_evaluations: 1` expected) so repeated peeking is visible.
Threshold and bands are computed from OOF train scores, never from test. Manifest excludes any
row-level data.

**Acceptance criteria**: `selection_matrix.csv` shows all criteria; decision recorded in
`models/manifest.json.selection_rationale` with reference to the matrix; threshold rule and
values in `threshold_and_bands.json`; test metrics table and figures present; manifest fields
per contract populated; two independent runs agree within tolerance recorded in
`docs/REPRODUCIBILITY.md` (PV-13).

**Computed, not narrated**: all tuning scores, selection matrix values, threshold, band
boundaries, test metrics, calibration statistics, reproduction deltas.

### M7. SHAP explainability, ethical-AI/fairness analysis, limitations, mitigation, and model card

**Creates/modifies**: `src/ssn/explain/shap_explain.py`, `src/ssn/explain/pdp_ice.py`,
`src/ssn/explain/language.py`, `src/ssn/fairness/{groups,metrics,audit,mitigate}.py`,
`src/ssn/reporting/model_card.py`, `notebooks/05_explainability_fairness.ipynb`,
`reports/explainability/shap_global_bar.png`, `reports/explainability/shap_beeswarm.png`,
`reports/explainability/shap_values_test.npz`, `reports/explainability/shap_local_examples.md`,
`reports/explainability/pdp_ice_<feature>.png`, `reports/fairness/group_metrics.csv`,
`reports/fairness/group_metrics.json`, `reports/fairness/group_calibration.png`,
`reports/fairness/mitigation_comparison.csv`, `reports/model_card.md`,
`tests/unit/test_fairness_metrics.py` (hand-computed expectations),
`tests/unit/test_groups_min_size.py`, `tests/unit/test_language_no_sensitive_reasons.py`.

**Inputs**: `models/final_pipeline.joblib`, test features and evaluator labels (fairness audit
reads `data/evaluation/demo_cohort_labels.parquet` and test parquet), `configs/language.yaml`.

**Outputs**: SHAP global/local artifacts; PDP/ICE for continuous features judged suitable
(list with reasons in notebook); fairness tables with `n` per group and `reliable` flag;
mitigation comparison (baseline vs at least one of reweighting, per-group threshold, or
post-processing) on fairness and performance; model card rendered from manifest and results;
limitations section text with computed references.

**Dependencies**: M6.

**Tests / verification**:

```bash
python -m ssn explain --config configs/base.yaml
python -m ssn fairness audit --config configs/base.yaml
python -m ssn fairness mitigate --config configs/base.yaml
python -m ssn model-card --config configs/base.yaml
pytest -q tests/unit/test_fairness_metrics.py tests/unit/test_groups_min_size.py tests/unit/test_language_no_sensitive_reasons.py
```

**Privacy / leakage checks**: `language.yaml` maps sensitive attributes (gender, age, and any
other audited field) to `adviser_visible: false`; `test_language_no_sensitive_reasons.py`
asserts local explanation rendering drops them. Fairness outputs are aggregate only (no
`record_id` in `reports/fairness/*`). Gender encoding used in `groups.py` must be marked
`verified: true` in `data/data_dictionary.md` or the command exits with an error (PV-04).

**Acceptance criteria**: FR-040 to FR-050 satisfied; each group row has `n` and a warning when
`n < min_group_size`; residual-risk paragraph present; model card contains every field in
contracts/artifact-manifest.md plus fairness summary; no claim of "fair" without qualification
(scanner checks `reports/model_card.md` and `final_report.md` for the bare phrase "the model is
fair").

**Computed, not narrated**: SHAP importances and example local explanations; PDP/ICE curves;
every fairness metric and `n`; mitigation deltas; age-band boundaries chosen (PV-06) and group
sizes (PV-07).

### M8. Final written report plus technical and business 8-12-slide decks

**Creates/modifies**: `reports/final_report.md`, `reports/rubric_map.md`
(`src/ssn/reporting/rubric_map.py` generates the skeleton), `notebooks/90_technical_deck.ipynb`,
`reports/decks/technical_deck.slides.html`, `reports/decks/business_deck_outline.md`,
`reports/decks/business_deck.pptx` (authored in PowerPoint/Canva from exported figures and
computed tables), export of final report to PDF or DOCX for submission, README completion.

**Inputs**: every table, figure, and JSON under `reports/`, `models/manifest.json`.

**Outputs**: final report with rubric map and Bias & Fairness Analysis section; two decks.

**Dependencies**: M7.

**Tests / verification**:

```bash
python -m ssn rubric-map --config configs/base.yaml           # regenerates skeleton with links
jupyter nbconvert notebooks/90_technical_deck.ipynb --to slides --output-dir reports/decks
python - <<'PY'
import re,io
html=open('reports/decks/technical_deck.slides.html').read()
n=len(re.findall(r'<section', html)); print("technical slides:", n); assert 8<=n<=12
PY
python -m ssn scan-language --paths reports/ README.md          # prohibited terms + unlabeled ROI figures
pandoc reports/final_report.md -o reports/final_report.pdf     # if pandoc available; else export via editor
```

**Privacy / leakage checks**: `scan-language` flags currency or percentage figures near
"ROI", "saving", "value", or "capacity" lacking an "illustrative"/"assumption" label within the
same paragraph; report contains no raw rows or identifiers.

**Acceptance criteria**: Report sections cover Steps 1-7 and optional steps attempted; rubric map
links every criterion; each deck has 8-12 slides (business deck count checked manually and
recorded in `business_deck_outline.md`); all numbers in report and decks trace to a file under
`reports/` or `models/manifest.json`.

**Computed, not narrated**: every metric, count, fairness value, and figure; the business deck's
illustrative KPI (share of eventual dropout cases reached at capacity K) must be read from
`reports/tables/test_recall_precision_at_k.csv`.

### M9. Optional Dash deployment: Student Success Navigator

**Creates/modifies**: `src/ssn/app/**` (see structure), `configs/base.yaml` (app section:
`host`, `port`, `capacity_k`, `bands`), `docs/DEPLOYMENT.md`, `tests/app/test_no_labels_rendered.py`,
`tests/app/test_version_check.py`, `tests/app/test_actions_log.py`,
`tests/app/test_new_record_validation.py`, `tests/app/test_forbidden_imports.py`,
`tests/app/test_top_k_ranking.py`, `reports/decks/demo.gif` (or screencast link).

**Inputs**: `models/final_pipeline.joblib`, `models/manifest.json`, `data/demo/demo_cohort.parquet`,
`reports/fairness/group_metrics.json`, `reports/explainability/shap_values_test.npz` (or
on-the-fly SHAP for the demo cohort at startup), `configs/language.yaml`.

**Outputs**: running app on localhost with six pages; SQLite action log at
`data/local/actions.sqlite`; deployment guide; demo media.

**Dependencies**: M7 (artifacts), M6 (manifest).

**Design constraints (from user input and spec)**:

- The app MUST load `final_pipeline.joblib` and call `predict_proba` only; there is no `fit`
  call anywhere under `src/ssn/app/` (asserted by `test_forbidden_imports.py` via AST scan for
  `.fit(`).
- The app reads `data/demo/demo_cohort.parquet` only. It MUST NOT import `ssn.modeling.evaluate`,
  `ssn.fairness.audit`, or open any path under `data/evaluation/` or `data/processed/`
  (AST and path-string scan in `test_forbidden_imports.py`).
- Support Queue: ranks by score descending, tie-break by `record_id` ascending (deterministic,
  documented), shows top `capacity_k` with notice when K > cohort size.
- Risk bands and threshold come from `models/manifest.json`, never recomputed in the app.
- Student Review: local SHAP contributions mapped through `language.yaml`; sensitive attributes
  filtered out; disclaimer component on every page.
- New Record Scoring: form fields generated from the allow-list with ranges from
  `data/data_dictionary.md` export (`configs/ranges.json` generated in M2); server-side validation.
- Equity Dashboard: renders `reports/fairness/group_metrics.json` only, with `n` and warnings.
- Model Card page: renders `reports/model_card.md`.
- Action log: append-only insert with timestamp, `record_id`, action, `acknowledged` boolean,
  optional reason, `model_version`; no update/delete statements in code.
- Version check: `manifest.model_version` must equal `configs/base.yaml: app.expected_model_version`
  or the app renders a blocking message and serves no scores.

**Tests / verification**:

```bash
pytest -q tests/app
python -m ssn app --config configs/base.yaml                  # http://127.0.0.1:8050
# manual: visit six pages; confirm disclaimer, K records, acknowledgement modal, no outcomes
sqlite3 data/local/actions.sqlite '.schema' && git check-ignore data/local/actions.sqlite
```

**Privacy / leakage checks**: `test_no_labels_rendered.py` renders every page layout with the
demo cohort and asserts the strings `Target`, `is_dropout`, `Dropout`, `Graduate`, `Enrolled`
(as outcome labels) and any column marked `adviser_visible: false` never appear;
`test_forbidden_imports.py` as above; `test_actions_log.py` asserts append-only and Git-ignored.

**Acceptance criteria**: FR-058 to FR-071 satisfied; SC-006, SC-007, SC-008 verified;
`docs/DEPLOYMENT.md` reproduces a running app from a fresh clone; demo media recorded.

**Computed, not narrated**: scores, bands, top-K list, explanation contributions, equity
metrics all originate from the saved pipeline and saved results files.

### M10. Optional MLOps/GenAI documentation and demonstration media

**Creates/modifies**: `docs/MLOPS.md` (environment reproducibility, config-driven runs,
manifest-based versioning and rollback plan, CI, basic monitoring plan for score drift and
group selection-rate drift), `.github/workflows/ci.yml` (ruff + pytest on push),
`Dockerfile` and `docker-compose.yml` (optional; app + artifacts), `docs/GENAI_USE.md` (tool,
purpose, prompts/examples, human review, limitations; or "not used"), `reports/decks/demo.gif`
or screencast link, README updates.

**Inputs**: all prior milestones.

**Outputs**: CI passing badge; documented rollback plan referencing `models/manifest.json`
versions; GenAI documentation.

**Dependencies**: M9 for app demo; M6 for manifest.

**Tests / verification**:

```bash
docker build -t ssn . && docker run --rm -p 8050:8050 ssn      # if Docker chosen
gh run list --limit 1                                          # CI status, if pushed
python -m ssn scan-language --paths docs/
```

**Privacy / leakage checks**: Docker image copies `models/` and `data/demo/` only; never
`data/evaluation/`, `data/processed/`, `data/raw/`, or `data/local/` (`.dockerignore` asserted
in `tests/unit/test_dockerignore.py` if Docker is used). GenAI documentation confirms no raw
student rows were sent to external services (FR-021).

**Acceptance criteria**: FR-072 to FR-074 satisfied for each optional item attempted, or the
item is recorded as "not attempted" in README and final report.

**Computed, not narrated**: CI run results; container build output; drift-monitoring plan
thresholds must reference computed baseline selection rates from `reports/fairness/`.

## Milestone Dependency Graph

```text
M1 -> M2 -> M3 -> M4 -> M5 -> M6 -> M7 -> M8
                                    M7 -> M9 -> M10
```

M9 and M10 are optional; M8 can proceed in parallel with M9 once M7 completes.
