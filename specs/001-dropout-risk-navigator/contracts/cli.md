# Contract: Command-Line Interface (`python -m ssn <command>`)

All commands accept `--config PATH` (default `configs/base.yaml`) and `--log-level`. Exit code 0
on success, 2 on config/validation error, 3 on `LeakageError`, 4 on privacy violation (e.g. label
column in adviser-facing output). Each command writes only to the directories listed; anything
else is a defect.

| Command | Reads | Writes | Notes |
|---------|-------|--------|-------|
| `config validate` | configs | stdout | Schema check; prints resolved seed and illustrative flags |
| `data download` | network (UCI) | `data/raw/data.csv` | Verifies sha256 against config; refuses on mismatch |
| `data validate` | `data/raw/data.csv`, `features.yaml` | stdout, `reports/tables/validate_report.json` | Column set, dtypes, Target labels, classification completeness |
| `data profile` | raw | `reports/tables/profile_*.csv`, `configs/ranges.json` | Per-column stats; ranges feed app validation |
| `data clean` | raw | `data/processed/clean.parquet`, `reports/tables/clean_before_after.csv` | Documented treatments |
| `data split` | clean | `data/processed/{train,test}.parquet`, `data/demo/demo_cohort.parquet`, `data/evaluation/demo_cohort_labels.parquet` | Stratified, seeded; demo has no labels |
| `eda` | train (and analysis-only view of raw for second-semester plots) | `reports/figures/eda_*.png`, `reports/tables/eda_*.csv` | Second-semester plots prefixed `analysis_only_` |
| `select` | train | `reports/tables/selection_*.csv`, `reports/tables/selection_decision.json` | Filter + embedded inside CV |
| `pca` | train | `reports/tables/pca_*.csv`, `reports/figures/pca_*.png` | Fit inside folds |
| `train-cv --models ...` | train | `reports/tables/cv_comparison.csv`, `data/processed/oof_<model>.parquet`, `reports/figures/cv_pr_curves.png` | Dummy always included |
| `tune --models ...` | train | `reports/tables/tuning_results_<model>.csv` | RandomizedSearchCV |
| `select-model` | cv tables, oof, fairness prelim | `reports/tables/selection_matrix.csv`, decision appended to manifest draft | Accuracy excluded from matrix |
| `threshold` | oof of selected model | `reports/tables/threshold_and_bands.json` | Capacity-aware; never reads test |
| `calibrate` | train | `reports/tables/calibration_comparison.csv` | Chooses calibrated variant per R-10 |
| `fit-final` | train | `models/final_pipeline.joblib`, `models/manifest.json` | Refit on full train; `n_jobs=1` |
| `evaluate-test` | test, evaluator labels, pipeline | `reports/tables/test_*.csv`, `reports/figures/test_*.png`; increments `manifest.test_evaluations` | Intended to run once |
| `explain` | pipeline, test features | `reports/explainability/*` | SHAP, PDP/ICE |
| `fairness audit` | pipeline, test, evaluator labels | `reports/fairness/group_metrics.{csv,json}`, figures | Refuses if gender encoding unverified |
| `fairness mitigate` | as audit | `reports/fairness/mitigation_comparison.csv` | Not deployed |
| `model-card` | manifest, reports | `reports/model_card.md` | Rendered, never hand-edited numbers |
| `rubric-map` | reports tree | `reports/rubric_map.md` | Skeleton with links |
| `scan-language --paths ...` | files | stdout, exit 1 on findings | Prohibited terms, unlabeled business figures, bare "the model is fair" |
| `reproduce-check --runs-a DIR --runs-b DIR` | two `reports/` trees and their manifests | `docs/REPRODUCIBILITY.md` table | Records per-metric absolute deltas; exit 1 if any exceeds the tolerance recorded in that file |
| `app` | manifest, pipeline, demo cohort, language, fairness json | `data/local/actions.sqlite` | Serves Dash on configured host/port; no writes elsewhere |
| `actions export` | actions.sqlite | `data/local/actions_export.csv` | Local review only |

## Makefile targets (thin wrappers)

`make setup`, `make data` (download → validate → profile → clean → split), `make eda`,
`make select`, `make cv`, `make tune`, `make final` (select-model → threshold → calibrate →
fit-final → evaluate-test), `make explain`, `make fairness`, `make report`, `make app`,
`make test`, `make lint`, `make all` (everything except `app`).
