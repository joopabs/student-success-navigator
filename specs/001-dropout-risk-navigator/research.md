# Phase 0 Research: Fair and Explainable Student Dropout Risk Prediction

**Date**: 2026-09-09 | **Plan**: [plan.md](plan.md)

Each item records a decision, rationale, and alternatives. Facts marked **verified** were checked
against the UCI dataset page on 2026-09-09. Facts marked **to verify** are owned by a PV task in
the spec and MUST NOT be treated as established until that task records a result.

## R-01. Dataset provenance and licence

- **Verified (UCI page, 2026-09-09)**: Name "Predict Students' Dropout and Academic Success";
  licence Creative Commons Attribution 4.0 International (CC BY 4.0); 4,424 instances; 36
  features; donated 2021-12-12; creators Valentim Realinho, Mónica Vieira Martins, Jorge Machado,
  Luís Baptista (Instituto Politécnico de Portalegre); DOI 10.24432/C5MC89; no missing values
  declared; tabular CSV (`data.csv`, about 520.7 KB); classification with three imbalanced
  classes; recommended split 80% train / 20% test.
- **Recommended citation (verbatim from page)**: Realinho, V., Vieira Martins, M., Machado, J., &
  Baptista, L. (2021). Predict Students' Dropout and Academic Success [Dataset]. UCI Machine
  Learning Repository. https://doi.org/10.24432/C5MC89
- **Decision**: Record the above in `data/README.md` with access date and the sha256 of the
  downloaded CSV. CC BY 4.0 permits redistribution with attribution, but the raw file will still
  be Git-ignored and fetched by script to keep the "no data in Git" policy uniform (R-11).
- **To verify (PV-01, PV-02, PV-05)**: actual row/column counts, `Target` values, and the "no
  missing values" claim against the downloaded file.
- **Alternatives**: Kaggle mirror rejected because licence provenance is clearer at UCI.

## R-02. Language, packaging, and utility dependencies

- **Decision**: Python 3.11; `src/` layout with package `ssn`; `pyproject.toml` for metadata and
  tool config; `requirements.txt` pinned for graders; `requirements-dev.txt` for pytest, ruff,
  nbconvert. Add PyYAML (config) and pyarrow (parquet) as the only dependencies outside the list
  the user named. Both are small, standard utilities; YAML is the constitution's example config
  format and parquet preserves dtypes between pipeline stages.
- **Alternatives**: JSON configs (no comments, less readable); CSV intermediates (dtype loss,
  slower); Poetry/uv lockfiles (fine, but `requirements.txt` is a rubric-named deliverable).

## R-03. Configuration and seed propagation

- **Decision**: One `configs/base.yaml` holding `seed`, paths, split ratio, `capacity_k`,
  `window_sensitivity_weeks`, band rule, `min_group_size`, `illustrative_assumptions` block; per-model YAML
  under `configs/models/`. `ssn.config.load()` validates required keys and types, then sets
  `numpy` and `random` seeds and returns a frozen dataclass. Every sklearn estimator receives
  `random_state=cfg.seed`.
- **Rationale**: Constitution IV requires a single seed and config-driven runs.
- **Alternatives**: Hydra/OmegaConf (extra dependency, overkill for one project).

## R-04. Target derivation

- **Decision**: `is_dropout = (Target == "Dropout").astype(int)`; Enrolled and Graduate map to
  0. `ssn.data.schema` asserts the observed set of `Target` values equals exactly
  `{Dropout, Enrolled, Graduate}` before mapping; otherwise the pipeline halts (FR-005).
- **To verify (PV-02)**: exact spelling/casing of the labels in the CSV.
- **Alternatives**: Treat "Enrolled" as unknown and drop; rejected because PROJECT_DECISIONS
  fixes Enrolled as non-dropout for the deployed workflow.

## R-05. Column availability classification and the "ambiguous" class

- **Decision**: `configs/features.yaml` assigns every column one of `enrollment`,
  `first_semester`, `second_semester`, `outcome`, or `ambiguous`. Allow-list = `enrollment` +
  `first_semester`. `second_semester`, `outcome`, and `ambiguous` are excluded by default.
- **Why an "ambiguous" class**: several UCI columns describe a status whose timestamp is not
  documented (expected examples per public documentation: tuition fees up to date, debtor,
  scholarship holder). If such a status reflects the state at data-extraction time it may encode
  post-outcome information and leak. Default policy: exclude; run an ablation
  (`with_ambiguous` vs `without`) reported in the EDA report; include only if the source
  documentation confirms availability by end of first semester. Macro-economic indicators
  (expected: unemployment rate, inflation rate, GDP) are classified `enrollment` pending PV-03
  confirmation that they refer to the enrollment year.
- **To verify (PV-03)**: the full column list and each classification, reviewed against the UCI
  variables table and the source article (Realinho et al., 2022, *Data*, 7(11), 146).
- **Alternatives**: Include all non-second-semester columns; rejected as a leakage risk.

## R-06. Gradient boosting implementation

- **Decision**: scikit-learn `HistGradientBoostingClassifier` as the gradient-boosting candidate.
  It supports `class_weight`, early stopping, and native handling of missing values, and adds
  no dependency. XGBoost is recorded as an alternative to add only if HGB underperforms
  logistic regression on CV PR-AUC, which would be surprising and would be documented.
- **Rationale**: The user asked to keep dependencies to the named list; the spec allows
  "gradient boosting or XGBoost".
- **Alternatives**: XGBoost (extra dependency, `scale_pos_weight` for imbalance); LightGBM.

## R-07. Class imbalance treatment

- **Decision**: Primary treatment is `class_weight="balanced"` (LR, RF, HGB) plus
  capacity-aware thresholding. Secondary experiment: SMOTENC (categorical indices passed
  explicitly, so encoded categoricals are not interpolated) via `imblearn.pipeline.Pipeline`
  inside CV for LR and RF, reported in `cv_comparison.csv`. Selection prefers class weighting
  unless SMOTENC improves PR-AUC by more than one CV standard deviation, because weighting is
  simpler to maintain and does not synthesise student records.
- **To verify (PV-02)**: actual positive rate; if the minority class exceeds roughly 30% the
  SMOTE experiment may be dropped with a note.
- **Alternatives**: Random undersampling (discards data); focal loss (not in sklearn).

## R-08. Recall@K and Precision@K inside cross-validation

- **Decision**: K is defined at cohort level (the demo/test cohort). In CV, each validation fold
  uses `k_fold = round(K * n_fold / n_test_expected)` so the selection rate matches deployment.
  Report Recall@K and Precision@K for `capacity.k` and for each K derived from `capacity.window_sensitivity_weeks`.
- **Illustrative default (assumption, not a fact)**: capacity is `per_week: 10` over
  `window_weeks: 5`, giving `k: 50`; sensitivity uses windows of 2, 5, and 10 weeks (K = 20, 50,
  100). Framing K as weekly capacity times an outreach window makes the KPI readable as "share
  of eventual dropout cases reached within a 5-week outreach window" rather than a bare count.
  Every surface that shows these values carries the label "illustrative". PV-10 records the
  final choice.
- **Alternatives**: Percent-based K (harder to explain to advisers).

## R-09. Threshold and risk-band rule

- **Decision**: Compute the threshold on out-of-fold training scores as the score quantile that
  yields a selection rate equal to `capacity_k / n_test_expected`. Report the F1-optimal and
  recall-at-fixed-precision thresholds as sensitivity. Three bands derived from OOF score
  quantiles and saved in the manifest: top band boundary = the capacity threshold; middle band
  boundary = a documented second quantile (default: twice the capacity selection rate); remainder
  = standard. Band names are supportive: "Priority outreach", "Check-in suggested", "Standard
  support". The app never recomputes them.
- **Rationale**: Ties the operating point to outreach capacity as PROJECT_DECISIONS requires.
- **Alternatives**: Fixed 0.5 threshold (meaningless under imbalance); cost-based threshold
  (needs cost data we do not have).

## R-10. Calibration

- **Decision**: Compare uncalibrated versus `CalibratedClassifierCV` (isotonic and sigmoid)
  fitted within the training set with internal CV. Report Brier score, expected calibration error
  (10 bins), and reliability curves on OOF and once on test. Choose calibrated variant only if it
  improves Brier without reducing PR-AUC by more than one CV standard deviation.
- **Alternatives**: Report raw scores only; rejected because PROJECT_DECISIONS lists calibration.

## R-11. Data and artifact storage policy

- **Decision**: `data/raw`, `data/processed`, `data/demo`, `data/evaluation`, `data/local` are
  Git-ignored and regenerated by `make data`. All `models/*.joblib` files are Git-ignored;
  `make final` regenerates them and their sha256 is recorded in `models/manifest.json` (always
  committed), so graders can verify they rebuilt the same artifact. Figures and tables under
  `reports/` are committed because the report and decks reference them and graders need them
  without running code.
- **Alternatives**: Git LFS (adds tooling for graders); DVC (extra dependency).

## R-12. Explainability tooling

- **Decision**: `shap.TreeExplainer` for RF/HGB, `shap.LinearExplainer` for logistic regression
  (on the transformed feature space, with names recovered from `ColumnTransformer.get_feature_names_out`).
  If calibration is applied, the explainer runs on the fitted base estimator inside the
  `CalibratedClassifierCV` wrapper and the report states that explanations describe uncalibrated
  contributions. Fallback: `sklearn.inspection.permutation_importance`. PDP/ICE via
  `sklearn.inspection.PartialDependenceDisplay` for continuous features with sufficient support
  (rule: at least 10 distinct values; otherwise excluded with reason).
- **Alternatives**: LIME (kept optional); rejected as primary due to instability.

## R-13. Fairness metric implementation

- **Decision**: Implement group metrics in `ssn.fairness.metrics` with pandas/numpy: selection
  rate, demographic parity difference (max-min selection rate), disparate impact ratio (min/max
  selection rate), TPR, FPR, equal opportunity difference (max-min TPR), equalized odds summary
  (max of TPR and FPR differences), per-group Brier and reliability curve. Unit tests compare
  against hand-computed values on a fixture. Reference group for ratios = largest group,
  documented. `min_group_size` default 30 (assumption; PV-07 finalises); groups below it are
  flagged `reliable: false` and shown with a warning.
- **Rationale**: Avoids adding fairlearn; keeps arithmetic transparent for the report.
- **Alternatives**: fairlearn `MetricFrame` (clean API, extra dependency; can be cross-checked in
  a notebook without becoming a runtime dependency).

## R-14. Sensitive attributes and age bands

- **Decision**: Audit gender and age band. Gender grouping requires the encoding to be marked
  `verified: true` in `data/data_dictionary.md` after PV-04; otherwise the audit command refuses
  to run. Age bands are set after PV-06 profiling of the age-at-enrollment distribution; the
  provisional scheme to evaluate is four bands (traditional-age through mature students) with
  boundaries chosen to keep each band above `min_group_size` where possible and documented in
  `configs/base.yaml`. No boundaries are asserted here.
- **Alternatives**: Auditing nationality, marital status, or parental qualification; deferred
  unless ethically justified and sample sizes permit (spec FR-045).

## R-15. Mitigation experiment

- **Decision**: Compare the selected model against (a) sample reweighting by group and label and
  (b) group-specific thresholds that equalise selection rate at fixed total K. Report fairness
  and performance deltas in `reports/fairness/mitigation_comparison.csv`. Post-processing that
  uses sensitive attributes at inference time is reported but not deployed, because the app must
  not consume sensitive attributes for individual decisions (constitution X).
- **Alternatives**: Adversarial debiasing (out of scope); dropping proxies (weak evidence).

## R-16. Dash application architecture

- **Decision**: Dash Pages (`dash.register_page`) with one module per page; app factory in
  `ssn.app.app:create_app(cfg)`; services layer for scoring, explanations, actions, equity;
  disclaimer component injected into every page layout. Startup: load manifest, verify version,
  load pipeline with joblib, score demo cohort once, compute local SHAP for the demo cohort with
  the same explainer type as training (or load precomputed `shap_values_test.npz`), cache in
  memory. No `fit` calls; enforced by AST test.
- **Alternatives**: Streamlit (not the assignment's named option); Flask + templates (more
  boilerplate for interactive tables).

## R-17. Action log store

- **Decision**: SQLite file `data/local/actions.sqlite` created on first write, schema in
  contracts/action-log.md, append-only (INSERT only). CSV export command for review. Git-ignored
  via existing `*.sqlite` rule. If the path is unwritable the app shows a notice and continues
  read-only (spec edge case).
- **Alternatives**: CSV log (no schema, race-prone); Postgres (overkill).

## R-18. Neutral language mapping and scanning

- **Decision**: `configs/language.yaml` provides, per feature: `label` (adviser-facing phrase),
  `direction_phrases` for positive/negative SHAP contribution, and `adviser_visible` flag.
  Prohibited-term list includes "at risk of failing", "likely to drop out", "problem student",
  "failing student", "dropout risk" as an adviser-facing label (the internal model name may use
  "dropout" in code and technical docs). A CLI `scan-language` command scans app strings,
  reports, README, and docs.
- **Alternatives**: Hard-coding strings in pages (untestable, drifts).

## R-19. Reproducibility tolerance

- **Decision**: Run the full pipeline twice in fresh environments; record per-metric absolute
  differences in `docs/REPRODUCIBILITY.md` and set the tolerance to the observed maximum plus a
  small margin, with the expectation of exact equality for single-threaded RF/HGB with fixed
  seeds. `n_jobs` defaults to 1 for final fit to maximise determinism; CV may use more cores.
- **Alternatives**: Assert exact equality (may fail across BLAS builds).

## R-20. Presentation tooling

- **Decision**: Technical deck via `jupyter nbconvert --to slides` from
  `notebooks/90_technical_deck.ipynb` (assignment names Jupyter slides). Business deck authored
  in PowerPoint or Canva from `reports/decks/business_deck_outline.md`, which is generated with
  the computed figures and KPI values to paste. Final report in Markdown, exported to PDF via
  pandoc if available or via an editor otherwise.
- **Alternatives**: python-pptx generation (extra dependency, lower visual quality); LaTeX
  Beamer (fine, but nbconvert reuses the notebooks directly).

## R-21. Testing strategy for privacy and leakage

- **Decision**: Three layers. Unit: allow-list enforcement, target mapping, engineered features,
  fairness arithmetic, threshold/top-K logic, language scanner. Integration: pipeline on a
  synthetic fixture (never real rows) asserting fit isolation and reproducibility. App: layout
  rendering asserts no forbidden strings; AST scan for `.fit(` and forbidden imports/paths;
  append-only log behaviour; version mismatch blocks scoring.
- **Alternatives**: Manual review only; rejected because these are constitution gates.
