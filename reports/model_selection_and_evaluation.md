# Model Selection, Threshold, Calibration, and Held-Out Evaluation (Milestone 6)

**Generated:** 2026-09-10 from `reports/tables/tuned_params.json`, `tuning_results_*.csv`, `selection_matrix*.csv`,
`model_selection_decision.json`, `calibration_comparison.csv`, `calibration_decision.json`, `threshold_and_bands.json`,
`threshold_tradeoffs.csv`, `oof_recall_precision_at_k.csv`, `test_metrics*.csv`, `test_recall_precision_at_k.csv`,
and `models/manifest.json`. Figures: `oof_calibration.png`, `test_pr_curve.png`, `test_calibration.png`,
`test_confusion_matrix.png`.

> **Measured vs illustrative.** Every metric below is MEASURED on data (cross-validation on the training split,
> or the single held-out test evaluation). The outreach capacity (10 students per week over a
> 5-week window, K = 50) and any "share of dropouts reached" figure are ILLUSTRATIVE
> assumptions, not institutional facts. Nothing here is a claim of production readiness or causal impact.

## 1. Tuning (training split, 5-fold stratified CV, seed 42)

All three candidates were within one CV standard deviation of each other after Milestone 5, so all three were
tuned ("promising" = no candidate could be excluded on the evidence). RandomizedSearchCV, scoring = PR-AUC,
search spaces from `configs/models/*.yaml`, each in both selection settings.

| candidate | cv_pr_auc_mean | cv_pr_auc_std | n_iter | best_params |
|---|---|---|---|---|
| logreg__sel-none | 0.8186 | 0.0146 | 30 | {"C": 1.1219752813215704, "l1_ratio": 1.0} |
| logreg__sel-decided | 0.8115 | 0.0142 | 30 | {"C": 14.528246637516036, "l1_ratio": 1.0} |
| random_forest__sel-none | 0.8094 | 0.0112 | 40 | {"max_depth": 18, "max_features": "sqrt", "min_samples_leaf": 2} |
| random_forest__sel-decided | 0.8088 | 0.0110 | 40 | {"max_depth": 20, "max_features": "log2", "min_samples_leaf": 5} |
| hist_gb__sel-none | 0.8146 | 0.0149 | 40 | {"l2_regularization": 0.11044350847124683, "learning_rate": 0.06746437142284309, "max_leaf_nodes": 21, "min_samples_leaf": 36} |
| hist_gb__sel-decided | 0.8057 | 0.0153 | 40 | {"l2_regularization": 0.11044350847124683, "learning_rate": 0.06746437142284309, "max_leaf_nodes": 21, "min_samples_leaf": 36} |

## 2. Selection matrix (OOF on the training split with tuned parameters)

Criteria: PR-AUC (primary), Recall@K and Precision@K at the fold-scaled illustrative capacity, Brier, ECE,
preliminary fairness at the capacity threshold (max demographic-parity difference and min disparate-impact ratio
across gender and age band, reliable groups only), native SHAP support, maintainability, fit time.
**Accuracy is not a criterion** (constitution Principle VIII).

| candidate | pr_auc | pr_auc_std_cv | roc_auc | recall_at_k | precision_at_k | brier | ece | fairness_max_dp_difference | fairness_min_di_ratio | oof_fit_time_s_total |
|---|---|---|---|---|---|---|---|---|---|---|
| logreg__sel-none | 0.8173 | 0.0146 | 0.8772 | 0.1706 | 0.9700 | 0.1343 | 0.0938 | 0.1309 | 0.1436 | 0.5393 |
| hist_gb__sel-none | 0.8121 | 0.0149 | 0.8711 | 0.1724 | 0.9800 | 0.1320 | 0.0761 | 0.0812 | 0.3119 | 2.4286 |
| logreg__sel-decided | 0.8103 | 0.0142 | 0.8716 | 0.1706 | 0.9700 | 0.1370 | 0.0955 | 0.1262 | 0.1445 | 0.4162 |
| random_forest__sel-none | 0.8078 | 0.0112 | 0.8725 | 0.1715 | 0.9750 | 0.1286 | 0.0539 | 0.1107 | 0.2004 | 5.2767 |
| random_forest__sel-decided | 0.8066 | 0.0110 | 0.8711 | 0.1706 | 0.9700 | 0.1355 | 0.0895 | 0.1297 | 0.1447 | 3.6326 |
| hist_gb__sel-decided | 0.8029 | 0.0153 | 0.8636 | 0.1697 | 0.9650 | 0.1379 | 0.0885 | 0.0974 | 0.2376 | 1.6216 |

**Rule (from `model_selection_decision.json`):** 1) eligible = candidates whose OOF PR-AUC >= best PR-AUC - 1 x CV std of the best; 2) rank eligible by Recall@K (rounded to 3 dp, desc), then ECE (2 dp, asc), then fairness_max_dp_difference (2 dp, asc), then Brier (3 dp, asc), then OOF fit time (asc). Accuracy is not a criterion (constitution VIII). Explainability must be natively SHAP-supported.

**Ranked eligible candidates** (PR-AUC floor 0.8027):

| rank | candidate | pr_auc | recall_at_k | ece | fairness_max_dp_difference | brier | oof_fit_time_s_total |
|---|---|---|---|---|---|---|---|
| 1 | random_forest__sel-none | 0.8078 | 0.1715 | 0.0539 | 0.1107 | 0.1286 | 5.2767 |
| 2 | hist_gb__sel-none | 0.8121 | 0.1724 | 0.0761 | 0.0812 | 0.1320 | 2.4286 |
| 3 | logreg__sel-none | 0.8173 | 0.1706 | 0.0938 | 0.1309 | 0.1343 | 0.5393 |
| 4 | random_forest__sel-decided | 0.8066 | 0.1706 | 0.0895 | 0.1297 | 0.1355 | 3.6326 |
| 5 | logreg__sel-decided | 0.8103 | 0.1706 | 0.0955 | 0.1262 | 0.1370 | 0.4162 |
| 6 | hist_gb__sel-decided | 0.8029 | 0.1697 | 0.0885 | 0.0974 | 0.1379 | 1.6216 |

**Chosen: `random_forest__sel-none`.** random_forest__sel-none is within one CV standard deviation of the best OOF PR-AUC and ranks first under the documented lexicographic rule (Recall@K, then ECE, then demographic-parity gap, then Brier, then fit time). See selection_matrix_ranked.csv. In plain terms: the three model families are statistically
indistinguishable on PR-AUC, so the rule falls through to the ranking metric (tied at three decimals with gradient
boosting) and then to calibration error, where the random forest is clearly better (ECE 0.054 vs
0.076). Logistic regression, the PR-AUC leader, ranks third because of its calibration error
(0.094) and larger demographic-parity gap. The k = 30 selection variants all rank below their
all-feature counterparts.

## 3. Calibration (research R-10)

Nested: CalibratedClassifierCV (inner cv = 5) around the tuned pipeline, evaluated by outer OOF prediction.

| variant | pr_auc | brier | ece | recall_at_k | precision_at_k | mean_score |
|---|---|---|---|---|---|---|
| uncalibrated | 0.8078 | 0.1286 | 0.0539 | 0.1715 | 0.9750 | 0.3692 |
| isotonic | 0.8070 | 0.1251 | 0.0170 | 0.1706 | 0.9700 | 0.3213 |
| sigmoid | 0.8088 | 0.1253 | 0.0244 | 0.1715 | 0.9750 | 0.3216 |

**Decision:** applied = True, method = isotonic. Rule: apply the calibration method with the lowest Brier if it beats the uncalibrated Brier and its PR-AUC is not lower than uncalibrated PR-AUC minus one CV std. Calibration reduced ECE from
0.054 to 0.017 and Brier from 0.1286 to 0.1251 while leaving
PR-AUC within noise (0.8078 vs 0.8070). Calibration changes probability quality, not the
ranking that drives Recall@K.

## 4. Threshold and risk bands (OOF scores of the final, calibrated variant)

Rule `oof_quantile_for_capacity`: the threshold is the OOF score at which the selection rate equals K / cohort =
50 / 885 = 0.0565; on 3539 OOF rows that is the 200-th highest score,
**threshold = 0.9728**. The trade-off table shows what other rules would cost in false positives (students
contacted who would not have dropped out) and false negatives (dropouts not reached):

| rule | threshold | n_selected | selection_rate | precision | recall | f1 | false_positives | false_negatives | true_positives |
|---|---|---|---|---|---|---|---|---|---|
| capacity (chosen) | 0.9728 | 202 | 0.0571 | 0.9703 | 0.1724 | 0.2928 | 6 | 941 | 196 |
| f1_optimal | 0.3848 | 1154 | 0.3261 | 0.7106 | 0.7212 | 0.7158 | 334 | 317 | 820 |
| precision>=0.8 | 0.5355 | 861 | 0.2433 | 0.8002 | 0.6060 | 0.6897 | 172 | 448 | 689 |
| 0.5 (default) | 0.5000 | 922 | 0.2605 | 0.7874 | 0.6385 | 0.7052 | 196 | 411 | 726 |

The capacity rule is chosen because the tool's purpose is to fill a fixed, small outreach list with the students most
likely to benefit; at that operating point precision is high and false positives are few, while recall is bounded
by capacity, not by the model. The F1-optimal and 0.5 rules would select roughly 1154 to
922 students, far beyond the illustrative capacity.

**Risk bands** (supportive names; boundaries are OOF score quantiles, stored in the manifest, never recomputed by the app):

| Band | Score range | Share of OOF rows | Rule |
|---|---|---|---|
| Priority outreach | [0.9728, 1.0000] | 0.057 | score >= capacity threshold |
| Check-in suggested | [0.8412, 0.9728] | 0.056 | score >= threshold at 2 x capacity selection rate |
| Standard support | [0.0000, 0.8412] | 0.887 | remaining scores |

Capacity sensitivity on OOF (illustrative windows):

| window_weeks | capacity_k | k_scaled_to_train | recall_at_k | precision_at_k |
|---|---|---|---|---|
| 2 | 20 | 80 | 0.0704 | 1.0000 |
| 5 | 50 | 200 | 0.1706 | 0.9700 |
| 10 | 100 | 400 | 0.3325 | 0.9450 |

## 5. Persisted artifact

`models/final_pipeline.joblib` (Git-ignored; regenerate with `make final`) and `models/manifest.json` (committed).
The manifest records model version 1.0.0, git sha, config hash, pipeline sha256, Python
3.11.12, library versions, seed 42, the exact input schema (21 allow-listed
columns with documented codes or ranges), engineered features, excluded columns by reason, estimator class and
parameters, calibration, threshold and bands, CV summary, and the test-evaluation counter. `tests/unit/test_persist_manifest.py`
loads the artifact, verifies the checksum, rejects tampering and version mismatch, and predicts on a schema-conforming frame.

## 6. Held-out test evaluation (performed once; `test_evaluations` = 1)

All models were scored in ONE pass on the 885-record test split (positive rate 0.3209).
Each candidate uses the capacity threshold derived from its own OOF scores; the final model uses the manifest threshold.
K applied to the test cohort = 50.

| model | threshold | pr_auc | roc_auc | recall_at_k | precision_at_k | brier | ece | precision_at_threshold | recall_at_threshold | f1_at_threshold |
|---|---|---|---|---|---|---|---|---|---|---|
| final | 0.9728 | 0.8175 | 0.8919 | 0.1690 | 0.9600 | 0.1180 | 0.0336 | 0.9649 | 0.1937 | 0.3226 |
| dummy | 0.3213 | 0.3209 | 0.5000 | 0.0739 | 0.4200 | 0.2179 | 0.0004 | 0.3209 | 1.0000 | 0.4859 |
| hist_gb__sel-decided | 0.9682 | 0.8103 | 0.8778 | 0.1761 | 1.0000 | 0.1354 | 0.0930 | 1.0000 | 0.1690 | 0.2892 |
| hist_gb__sel-none | 0.9630 | 0.8174 | 0.8783 | 0.1761 | 1.0000 | 0.1309 | 0.0849 | 1.0000 | 0.1866 | 0.3145 |
| logreg__sel-decided | 0.9776 | 0.8050 | 0.8750 | 0.1761 | 1.0000 | 0.1382 | 0.1033 | 1.0000 | 0.1796 | 0.3045 |
| logreg__sel-none | 0.9816 | 0.8154 | 0.8775 | 0.1761 | 1.0000 | 0.1373 | 0.1014 | 1.0000 | 0.1690 | 0.2892 |
| random_forest__sel-decided | 0.9502 | 0.8163 | 0.8871 | 0.1761 | 1.0000 | 0.1321 | 0.0983 | 1.0000 | 0.1796 | 0.3045 |
| random_forest__sel-none | 0.9341 | 0.8161 | 0.8915 | 0.1690 | 0.9600 | 0.1235 | 0.0754 | 0.9677 | 0.2113 | 0.3468 |

**Final model on test:** PR-AUC 0.8175, ROC-AUC 0.8919, Brier 0.1180, ECE 0.0336. At the
capacity threshold it selects 57 of 885 students with precision 0.965
(confusion: TP 55, FP 2, FN 229, TN 599). The dummy baseline scores
PR-AUC 0.3209 (the base rate) and Precision@K 0.42. Test PR-AUC (0.8175) is consistent with the
CV estimate (0.8078 ± 0.0112), which is the expected sign that the selection process did not overfit
to validation folds.

### Illustrative business KPI (measured recall, illustrative capacity)

| window_weeks | capacity_k_illustrative | k_applied_to_test | recall_at_k_measured | precision_at_k_measured | dropouts_in_test |
|---|---|---|---|---|---|
| 2 | 20 | 20 | 0.0669 | 0.9500 | 284 |
| 5 | 50 | 50 | 0.1690 | 0.9600 | 284 |
| 10 | 100 | 100 | 0.3275 | 0.9300 | 284 |

Read as: "under the ILLUSTRATIVE assumption of 10 outreach conversations per week, a 5-week window
would reach a measured 16.9% of the students who eventually dropped out in the test cohort, with
96% of contacted students being eventual dropouts". The percentage of dropouts reached is bounded by
capacity (50 slots for 284 dropouts); a 10-week window reaches 32.7%. No cost, saving,
or return figure is asserted because the dataset contains none.

## 7. What this does and does not establish

- Establishes: on one institution's historical data, a calibrated random-forest pipeline restricted to
  enrollment-time and first-semester features ranks students so that a small outreach list is filled almost
  entirely with students who later dropped out, with held-out PR-AUC consistent with cross-validation.
- Does not establish: causal impact of outreach, transferability to another institution (including Philippine
  institutions), or production readiness. The recording time of three excluded financial columns remains
  unverified (`data/README.md`); the fairness audit (Milestone 7) has not yet been run on the test cohort;
  proxy features (parental occupation and qualification) are present and must be discussed there.
- Reproducibility: see `docs/REPRODUCIBILITY.md` (Milestone 6, T057) for the fresh-environment re-run deltas.
