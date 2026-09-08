# Data Model: Fair and Explainable Student Dropout Risk Prediction

**Date**: 2026-09-09 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

All entities are file-backed. Field names for source columns are placeholders until PV-01 and
PV-03 record the actual UCI column names; no encodings are asserted here.

## Entities

### SourceRecord (raw)

One row of `data/raw/data.csv`.

| Field | Type | Notes |
|-------|------|-------|
| `<36 source feature columns>` | int / float / categorical codes | Names and encodings from UCI variables table; recorded in `data/data_dictionary.md` (PV-01, PV-04) |
| `Target` | categorical | Expected values Dropout, Enrolled, Graduate (PV-02) |

Validation: expected column set matches `configs/features.yaml`; dtypes per `ssn.data.schema`;
`Target` in the expected set; row count recorded.

### ColumnClassification (configs/features.yaml)

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | Exact source column name |
| `availability` | enum | `enrollment`, `first_semester`, `second_semester`, `outcome`, `ambiguous` |
| `role` | enum | `feature`, `sensitive`, `target`, `id`, `excluded` |
| `dtype` | enum | `numeric`, `categorical`, `binary` |
| `adviser_visible` | bool | False for sensitive attributes |
| `note` | string | Source of classification, verification status |

Rules: every raw column appears exactly once; allow-list = `availability in {enrollment,
first_semester} and role == feature`; anything else is prohibited for the deployed model.

### CleanRecord (data/processed/clean.parquet)

SourceRecord after cleaning with `record_id` (synthetic UUID-like string generated with the
seeded RNG) and `is_dropout` (int 0/1). Cleaning log stored in
`reports/tables/clean_before_after.csv` with fields `issue`, `column`, `count_before`,
`count_after`, `treatment`.

### Split (data/processed/train.parquet, test.parquet)

Stratified on `is_dropout`, ratio from config (default 0.8/0.2), seed from config. Disjoint by
`record_id`. `test.parquet` is read only by `evaluate-test`, `fairness audit`, and `explain`.

### DemoCohort (data/demo/demo_cohort.parquet)

Adviser-facing view of the test split.

| Field | Type | Notes |
|-------|------|-------|
| `record_id` | string | Synthetic key |
| allow-listed feature columns | as source | Only `availability in {enrollment, first_semester}` and `role: feature` |

Forbidden fields: `Target`, `is_dropout`, any `second_semester` or `outcome` column, and any
`role: sensitive` column. Enforced by `tests/unit/test_split.py`.

### EvaluatorLabels (data/evaluation/demo_cohort_labels.parquet)

| Field | Type | Notes |
|-------|------|-------|
| `record_id` | string | Joins to DemoCohort |
| `is_dropout` | int | Evaluation-only |
| `Target` | categorical | Evaluation-only |
| sensitive columns (`role: sensitive`) | as source | Aggregate fairness auditing only; never rendered |

Access rule: never imported or read by any module under `src/ssn/app/` (AST/path test).

### EngineeredFeature

Produced by `ssn.features.engineering` transformer; each declares its input columns.

| Feature | Inputs (allow-listed) | Rule | Rationale |
|---------|-----------------------|------|-----------|
| `sem1_approval_rate` | 1st-sem approved, 1st-sem enrolled | approved / enrolled; 0 enrolled -> NaN then imputed, count logged | Academic progress signal |
| `sem1_evaluation_participation_rate` | 1st-sem evaluations, 1st-sem enrolled | evaluations / enrolled; same zero rule | Engagement signal |
| `sem1_non_evaluation_rate` | 1st-sem without evaluations, 1st-sem enrolled | without_eval / enrolled; same zero rule | Disengagement signal |
| `grade_diff_vs_admission` | 1st-sem grade, admission grade | sem1_grade - admission_grade (scale check in PV-05) | Change relative to entry |
| `age_band` | age at enrollment | Bands from `configs/base.yaml` (set after PV-06) | EDA and fairness grouping only; `adviser_visible: false` |
| workload / progression measures | 1st-sem enrolled, credited, approved | e.g. credited share, enrolled load | Documented in EDA report |

Exact source column names are filled after PV-01.

### ModelCandidate (configs/models/*.yaml)

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | `dummy`, `logreg`, `random_forest`, `hist_gb`, optional `svm` |
| `estimator` | string | sklearn class path |
| `params` | map | Fixed params incl. `class_weight`, `random_state` from seed |
| `search_space` | map | RandomizedSearchCV distributions |
| `n_iter` | int | Search budget |
| `use_selection` | bool | Whether selector step is included |
| `use_pca` | bool | PCA experiment flag |

### CVResult (reports/tables/cv_comparison.csv)

Per model: `pr_auc_mean/std`, `roc_auc_mean/std`, `recall_mean/std`, `precision_mean/std`,
`f1_mean/std`, `recall_at_k_mean/std`, `precision_at_k_mean/std`, `brier_mean/std`,
`accuracy_mean/std` (reported, not used for selection), `fit_time_s`.

### OOFPredictions (data/processed/oof_<model>.parquet)

`record_id`, `fold`, `y_true`, `score`. Used for threshold and band derivation and preliminary
fairness.

### ThresholdAndBands (reports/tables/threshold_and_bands.json, copied into manifest)

| Field | Type | Notes |
|-------|------|-------|
| `rule` | string | e.g. `oof_quantile_for_capacity` |
| `capacity_k` | int | Illustrative; labelled |
| `n_cohort_expected` | int | Test cohort size |
| `threshold` | float | Score at capacity selection rate |
| `bands` | list of {`name`, `lower`, `upper`} | Supportive names; computed boundaries |
| `sensitivity` | map | F1-optimal and other alternative thresholds |

### ModelArtifact (models/final_pipeline.joblib + models/manifest.json)

See contracts/artifact-manifest.md for the manifest schema. The joblib object is a fitted
`sklearn.pipeline.Pipeline` including preprocessing, optional selector, and estimator (and
calibration wrapper if chosen).

### SupportPriorityScore (in-memory in app; optional cache parquet under data/local/)

| Field | Type | Notes |
|-------|------|-------|
| `record_id` | string | |
| `score` | float [0,1] | `predict_proba[:, 1]` from saved pipeline |
| `band` | string | From manifest bands |
| `rank` | int | Descending score, tie-break `record_id` ascending |
| `model_version` | string | From manifest |

### LocalExplanation

| Field | Type | Notes |
|-------|------|-------|
| `record_id` | string | |
| `contributions` | list of {`feature`, `value`, `shap`} | Transformed feature space mapped back to source or engineered names |
| `rendered` | list of {`label`, `phrase`} | Via `configs/language.yaml`; sensitive attributes removed |

### FairnessGroupResult (reports/fairness/group_metrics.json)

| Field | Type | Notes |
|-------|------|-------|
| `attribute` | string | `gender`, `age_band`, others if justified |
| `group` | string | Verified label from data dictionary |
| `n` | int | Group size in evaluation cohort |
| `reliable` | bool | `n >= min_group_size` |
| `selection_rate`, `tpr`, `fpr`, `brier` | float | Per group at deployed threshold |
| `dp_difference`, `di_ratio`, `eo_difference`, `eq_odds_max_diff` | float | Attribute-level, reference = largest group |
| `calibration_curve` | list | Present only if `reliable` |

### SupportActionLogEntry (data/local/actions.sqlite)

See contracts/action-log.md. Append-only.

### ModelCard (reports/model_card.md)

Rendered from manifest, `test_metrics.csv`, `threshold_and_bands.json`,
`group_metrics.json`, and hand-written limitations. Fields listed in FR-068.

## Relationships

```text
SourceRecord --clean--> CleanRecord --split--> Split{train,test}
Split.test --project--> DemoCohort (features only) + EvaluatorLabels (labels only)
Split.train --cv--> OOFPredictions --derive--> ThresholdAndBands
Split.train --fit--> ModelArtifact
ModelArtifact + DemoCohort --predict--> SupportPriorityScore --explain--> LocalExplanation
ModelArtifact + Split.test + EvaluatorLabels --evaluate--> test metrics, FairnessGroupResult
SupportPriorityScore --adviser acknowledges--> SupportActionLogEntry (never back to model)
```

## State transitions

- **Column**: `unclassified` -> `classified` (M2) -> `allowed | prohibited` (derived).
- **Test set**: `unseen` -> `evaluated_once` (manifest `test_evaluations` increments; >1 is a
  reportable event).
- **Model version**: `candidate` -> `selected` -> `persisted` -> `served`; app serves only when
  `manifest.model_version == config.app.expected_model_version`.
- **Support action**: `suggested` -> `acknowledged` -> `recorded | dismissed | overridden`; all
  recorded as separate appended rows.
