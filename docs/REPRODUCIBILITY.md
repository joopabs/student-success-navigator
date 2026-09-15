# Reproducibility

**Checked:** 2026-09-15 05:55 UTC by `python -m ssn reproduce-check`.
**Run A:** `reports` · **Run B:** `/private/tmp/claude-502/-Users-jpabular-Development-Learning-Python-student-success-navigator/0b0c709c-630c-4ada-8048-dad8dd06d677/scratchpad/repro2/reports` · **Tolerance (max absolute delta):** 0.005
**Result:** PASS — largest observed delta 0

Both runs use the single seed in `configs/base.yaml`, config-driven commands, and `n_jobs=1` for the final fit.
Residual nondeterminism, if any, comes from parallel RandomizedSearchCV scheduling (results are seeded) and BLAS.

Run B is a scratch tree created for the check, not a directory kept in the repository. Recreate one by copying `configs/base.yaml`, pointing every `paths.*` key at a scratch directory, and running the pipeline stages against that config; every pipeline output is config-driven, so the run leaves the repository untouched.

## Largest delta per file

| file | max abs delta |
|---|---|
| calibration_comparison.csv | 0 |
| cv_comparison.csv | 0 |
| pca_vs_nopca_cv.csv | 0 |
| selection_cv_by_k.csv | 0 |
| selection_matrix.csv | 0 |
| test_metrics.csv | 0 |
| test_metrics_all_models.csv | 0 |
| test_recall_precision_at_k.csv | 0 |
| threshold_and_bands.json | 0 |
| tuned_params.json | 0 |

## Top 15 deltas

| file | column | max abs delta |
|---|---|---|
| cv_comparison.csv | seed | 0 |
| threshold_and_bands.json | tradeoffs.2.false_positives | 0 |
| threshold_and_bands.json | tradeoffs.2.true_positives | 0 |
| threshold_and_bands.json | tradeoffs.3.threshold | 0 |
| threshold_and_bands.json | tradeoffs.3.n_selected | 0 |
| threshold_and_bands.json | tradeoffs.3.selection_rate | 0 |
| threshold_and_bands.json | tradeoffs.3.precision | 0 |
| threshold_and_bands.json | tradeoffs.3.recall | 0 |
| threshold_and_bands.json | tradeoffs.3.f1 | 0 |
| threshold_and_bands.json | tradeoffs.3.false_positives | 0 |
| threshold_and_bands.json | tradeoffs.3.false_negatives | 0 |
| threshold_and_bands.json | tradeoffs.3.true_positives | 0 |
| calibration_comparison.csv | pr_auc | 0 |
| calibration_comparison.csv | pr_auc_std_cv_uncalibrated | 0 |
| calibration_comparison.csv | roc_auc | 0 |
