# Model Card — Student Success Navigator support-priority model

**Version:** 1.0.0 · **Built:** 2026-09-09T19:26:38Z · **Git:** `950d30353270` ·
**Rendered:** 2026-09-10 06:34 UTC by `python -m ssn model-card` · **Held-out evaluations:** 1

> Scores are illustrative decision support for voluntary, supportive adviser outreach. They are not causal, not a judgement of a student, and not production-ready without institutional validation. All outreach decisions require qualified human review.

## Intended use

Decision support for voluntary, supportive adviser outreach after the first semester. The score ranks students for a **voluntary, supportive** adviser conversation
within a limited outreach capacity. It is decision support for qualified staff, reviewed case by case.

## Out-of-scope use (prohibited)

No automated or adverse decisions about admission, enrollment, scholarships, financial aid, grades, discipline, housing, or student opportunities. The score is not a prediction about a student's ability or worth and must not be
shown to students as such.

## Data

- **Source:** UCI ML Repository dataset 697, DOI 10.24432/C5MC89, licence CC BY 4.0;
  one higher-education institution; not representative of Philippine or other institutions.
- **Training / test:** 3539 / 885 student records (positive rate
  0.3213 / 0.3209); stratified split, seed 42.
- **Target:** `is_dropout` = 1 where source Target = Dropout; Enrolled, Graduate = 0.
- **Inputs (21 source columns + 7 engineered):** enrollment-time and first-semester
  information only. Excluded: 6 second-semester columns (after the prediction point),
  3 financial-status columns with undocumented timing (Debtor, Scholarship holder, Tuition fees up to date), and
  6 sensitive attributes used for auditing only (Age at enrollment, Educational special needs, Gender, International, Marital status, Nacionality).

## Model

- **Estimator:** `sklearn.ensemble.RandomForestClassifier` inside a scikit-learn pipeline (median imputation, scaling,
  one-hot encoding, stateless first-semester feature engineering). Selection setting: all features.
- **Imbalance:** class_weight (SMOTENC rejected under research R-07; see reports/model_comparison_cv.md).
- **Calibration:** applied (isotonic).
- **Selection rationale:** random_forest__sel-none is within one CV standard deviation of the best OOF PR-AUC and ranks first under the documented lexicographic rule (Recall@K, then ECE, then demographic-parity gap, then Brier, then fit time). See selection_matrix_ranked.csv. Rule: 1) eligible = candidates whose OOF PR-AUC >= best PR-AUC - 1 x CV std of the best; 2) rank eligible by Recall@K (rounded to 3 dp, desc), then ECE (2 dp, asc), then fairness_max_dp_difference (2 dp, asc), then Brier (3 dp, asc), then OOF fit time (asc). Accuracy is not a criterion (constitution VIII). Explainability must be natively SHAP-supported.
- **Environment:** Python 3.11.12; scikit-learn 1.9.0, numpy 2.4.6, pandas 3.0.5, shap 0.51.0, imbalanced-learn 0.14.2, joblib 1.6.0, ssn 0.1.0.

## Operating point (illustrative capacity, measured behaviour)

Capacity assumption: **10 students per week over 5 weeks = K 50** per cohort of
885 (ILLUSTRATIVE). Rule `oof_quantile_for_capacity` gives **threshold 0.9728** (OOF selection rate 0.0565).

| Band | Score range | Rule |
|---|---|---|
| Priority outreach | [0.9728, 1.0000] | score >= capacity threshold |
| Check-in suggested | [0.8412, 0.9728] | score >= threshold at 2 x capacity selection rate |
| Standard support | [0.0000, 0.8412] | remaining scores |

## Performance (measured)

Cross-validation on the training split: PR-AUC 0.8078 ± 0.0112,
Recall@K 0.1715, Brier 0.1286, ECE 0.0539.

Held-out test (single evaluation, n = 885):

| PR-AUC | ROC-AUC | Recall@K | Precision@K | Brier | ECE | Precision at threshold | Recall at threshold |
|---|---|---|---|---|---|---|---|
| 0.8175 | 0.8919 | 0.1690 | 0.9600 | 0.1180 | 0.0336 | 0.9649 | 0.1937 |

Recall@K is bounded by capacity: K = 50 slots for 284 eventual dropouts in the test cohort.
Capacity sensitivity (measured recall, illustrative windows):

| window_weeks | capacity_k_illustrative | recall_at_k_measured | precision_at_k_measured |
|---|---|---|---|
| 2 | 20 | 0.0669 | 0.9500 |
| 5 | 50 | 0.1690 | 0.9600 |
| 10 | 100 | 0.3275 | 0.9300 |

Zero predicted positives on test: False.

## Explainability

shap.TreeExplainer on the 5 calibrated ensemble members; one-hot columns summed per source column; averaged over calibrated ensemble members; explains uncalibrated base-estimator score contributions, not the calibrated probability. Outputs under `reports/explainability/`. Sensitive attributes are never shown as reasons.

## Fairness (aggregate audit)

Audited on the held-out cohort (n = 885) by gender, age_band; gender encoding {'1': 'male', '0': 'female'} verified = True. Groups with n < 30 are flagged unreliable.

| attribute | reference_group | n_reliable_groups | dp_difference | di_ratio | eo_difference | eq_odds_max_diff |
|---|---|---|---|---|---|---|
| gender | female | 2 | 0.0399 | 0.5584 | 0.0098 | 0.0098 |
| age_band | 17-19 | 4 | 0.2272 | 0.0803 | 0.3974 | 0.3974 |

| attribute | group | n | reliable | base_rate | selection_rate | tpr | fpr | brier |
|---|---|---|---|---|---|---|---|---|
| gender | female | 575 | True | 0.2452 | 0.0504 | 0.1986 | 0.0023 | 0.1081 |
| gender | male | 310 | True | 0.4613 | 0.0903 | 0.1888 | 0.0060 | 0.1364 |
| age_band | 17-19 | 403 | True | 0.1935 | 0.0199 | 0.1026 | 0.0000 | 0.0963 |
| age_band | 20-24 | 256 | True | 0.3086 | 0.0352 | 0.1139 | 0.0000 | 0.1468 |
| age_band | 25-34 | 141 | True | 0.6028 | 0.1348 | 0.2000 | 0.0357 | 0.1378 |
| age_band | 35+ | 85 | True | 0.4941 | 0.2471 | 0.5000 | 0.0000 | 0.1014 |

These numbers describe observed disparities at the deployed operating point; they do not, by themselves, establish that the model treats groups fairly. Full discussion, mitigation results and residual risks: `reports/bias_fairness_analysis.md`.

## Limitations, risks and human oversight

**Dataset scope and external validity.** One Portuguese higher-education institution, historical records published by
UCI (dataset 697, CC BY 4.0). Results describe this institution's past students and do not transfer to Philippine or other
institutions without new data, re-training, and a new audit. Predicted risk is a statistical association, not a cause.

**Historical bias and proxies.** The label is what happened, including whatever support students did or did not receive.
Sensitive attributes are excluded from the model, but parental qualification and occupation (four columns), application
route, programme, and attendance schedule act as proxies for age and socioeconomic background. The fairness audit found
near-equal true-positive rates by gender but a large equal-opportunity gap by age (TPR 0.10 for 17-19 vs 0.50 for 35+
at the deployed threshold; `reports/fairness/group_metrics.csv`). Younger students who later drop out are under-reached.

**Temporal leakage controls and their cost.** Only enrollment-time and first-semester columns are model inputs; the six
second-semester columns are prohibited and tested. Three financial-status columns (Debtor, Tuition fees up to date,
Scholarship holder) have undocumented recording time and are excluded; including them would raise CV PR-AUC by about
0.036 to 0.039 (`reports/tables/ablation_ambiguous.csv`), a gain that may be leakage. The source article
could not be retrieved programmatically to settle this (`data/README.md`, open item).

**Class imbalance.** A 0.32 positive (dropout) rate in both splits. Handled with class weighting (SMOTENC rejected under the documented rule),
PR-AUC as the primary metric, and a capacity-based threshold rather than 0.5.

**Overfitting and uncertainty.** Fold-to-fold PR-AUC standard deviation is about 0.011 to 0.017, the same order as the
differences between candidate models, so the model choice rests on secondary criteria (calibration) and is documented as
such. Held-out PR-AUC (0.8175) matches the CV estimate (0.8078), which argues against selection overfitting.
The test set was evaluated once; the manifest counter records it. A second fresh-environment run reproduced every table
exactly (`docs/REPRODUCIBILITY.md`).

**Capacity assumption.** K = 50 (10 per week × 5 weeks) is illustrative. Recall@K is bounded by it
(0.169 on test for 284 dropouts); it is a statement about capacity, not model quality. No cost, saving, or return figure is
asserted anywhere because the data contain none.

**Explanations.** SHAP values describe the uncalibrated ensemble members' contributions, aggregated per source feature and
averaged; they are not the calibrated probability and not causal. Engineered features cannot be varied independently for
PDP, so they are explained through SHAP only.

**Human oversight.** The tool proposes a short outreach list; a qualified adviser reviews each record, may dismiss or
override any suggestion, and records the decision locally. No automated or adverse decision is made or recommended.
Advisers should keep independent referral routes, especially for first-year students where model recall is lowest, and
the Equity Dashboard should be reviewed each outreach cycle.

## Provenance

Config sha256 `463b011689980e73…`, pipeline sha256 `e969a32296f617e5…`, raw data sha256
`3ef126de5cefff26…`. Reproduction: `docs/REPRODUCIBILITY.md`. cv_summary and test_summary are MEASURED on data; capacity_k, window_weeks and any share-of-dropouts-reached figure are ILLUSTRATIVE assumptions.
