# Model Comparison under Cross-Validation (Milestone 5)

**Generated:** 2026-09-10 from `reports/tables/cv_comparison.csv`, `cv_confusion.csv`, `ablation_ambiguous.csv`,
`ablation_sensitive.csv`, figures `cv_pr_curves.png`, `cv_calibration.png`, and the OOF parquet files under
`data/processed/`. Notebook: `notebooks/04_model_comparison.ipynb`.

**Scope.** Validation comparison only. Every pipeline (preprocessing, optional selector, optional SMOTENC,
estimator) was fitted inside 5-fold stratified cross-validation on the 3539-record training
split with seed 42. The held-out test split was not opened (spied in `tests/integration/test_cv_fixture.py`).
**No final model is selected here**; Milestone 6 applies the multi-criteria selection matrix.

## 1. Design

| Item | Setting |
|---|---|
| Baseline | `DummyClassifier(strategy=prior)`: constant score = training positive rate |
| Candidates | class-weighted Logistic Regression (liblinear); Random Forest (500 trees, `balanced_subsample`); HistGradientBoosting (`class_weight=balanced`, early stopping) |
| Variants | selection ∈ {none, decided (embedded L1, k=30 from Milestone 4)}; imbalance ∈ {class weighting, SMOTENC (LR and RF only, research R-07)} |
| Primary metric | PR-AUC (average precision) on out-of-fold scores |
| Ranking metrics | Recall@K, Precision@K with K = 10 per week × 5 weeks = 50 (ILLUSTRATIVE), scaled to each fold as k = round(K · n_fold / 885) = 40; sensitivity for [2, 5, 10]-week windows |
| Secondary | ROC-AUC, Brier, ECE (10 bins), precision / recall / F1 / accuracy at 0.5, confusion matrices at 0.5 and at K (summed over folds) |
| Runtime | mean fit time per fold recorded per variant |

Accuracy at 0.5 is reported for transparency only and is excluded from the Milestone 6 selection matrix
(constitution Principle VIII).

## 2. Comparison table (fold mean ± std, sorted by PR-AUC)

| variant | pr_auc_mean | pr_auc_std | roc_auc_mean | roc_auc_std | recall_at_k_mean | precision_at_k_mean | brier_mean | ece_mean | fit_time_s_mean |
|---|---|---|---|---|---|---|---|---|---|
| logreg__sel-none__imb-class_weight | 0.8182 | 0.0166 | 0.8777 | 0.0125 | 0.1706 | 0.9700 | 0.1344 | 0.0961 | 0.0313 |
| logreg__sel-decided__imb-class_weight | 0.8111 | 0.0172 | 0.8729 | 0.0120 | 0.1706 | 0.9700 | 0.1364 | 0.0984 | 0.0751 |
| hist_gb__sel-none__imb-class_weight | 0.8109 | 0.0144 | 0.8694 | 0.0104 | 0.1733 | 0.9850 | 0.1316 | 0.0667 | 0.5286 |
| logreg__sel-none__imb-smotenc | 0.8098 | 0.0172 | 0.8720 | 0.0126 | 0.1689 | 0.9600 | 0.1259 | 0.0422 | 1.5291 |
| hist_gb__sel-decided__imb-class_weight | 0.8076 | 0.0160 | 0.8652 | 0.0167 | 0.1741 | 0.9900 | 0.1365 | 0.0808 | 0.4238 |
| random_forest__sel-none__imb-class_weight | 0.8070 | 0.0094 | 0.8724 | 0.0103 | 0.1689 | 0.9600 | 0.1260 | 0.0321 | 1.1448 |
| random_forest__sel-none__imb-smotenc | 0.8032 | 0.0092 | 0.8685 | 0.0103 | 0.1715 | 0.9750 | 0.1299 | 0.0546 | 2.9090 |
| logreg__sel-decided__imb-smotenc | 0.8024 | 0.0194 | 0.8656 | 0.0107 | 0.1698 | 0.9650 | 0.1386 | 0.0967 | 0.1757 |
| random_forest__sel-decided__imb-class_weight | 0.7823 | 0.0136 | 0.8599 | 0.0122 | 0.1698 | 0.9650 | 0.1344 | 0.0470 | 0.8996 |
| random_forest__sel-decided__imb-smotenc | 0.7703 | 0.0196 | 0.8525 | 0.0117 | 0.1698 | 0.9650 | 0.1415 | 0.0598 | 1.2020 |
| dummy__sel-none__imb-none | 0.3213 | 0.0007 | 0.5000 | 0.0000 | 0.0572 | 0.3250 | 0.2181 | 0.0008 | 0.0211 |

Configuration per variant (estimator, key parameters, pipeline steps):

| variant | estimator | key_params | steps | seed | n_folds |
|---|---|---|---|---|---|
| dummy__sel-none__imb-none | sklearn.dummy.DummyClassifier | strategy=prior | pre>clf | 42 | 5 |
| logreg__sel-none__imb-class_weight | sklearn.linear_model.LogisticRegression | C=1.0;class_weight=balanced | pre>clf | 42 | 5 |
| logreg__sel-none__imb-smotenc | sklearn.linear_model.LogisticRegression | C=1.0;class_weight=balanced | pre>smote>clf | 42 | 5 |
| logreg__sel-decided__imb-class_weight | sklearn.linear_model.LogisticRegression | C=1.0;class_weight=balanced | pre>select>clf | 42 | 5 |
| logreg__sel-decided__imb-smotenc | sklearn.linear_model.LogisticRegression | C=1.0;class_weight=balanced | pre>select>smote>clf | 42 | 5 |
| random_forest__sel-none__imb-class_weight | sklearn.ensemble.RandomForestClassifier | class_weight=balanced_subsample;n_estimators=500 | pre>clf | 42 | 5 |
| random_forest__sel-none__imb-smotenc | sklearn.ensemble.RandomForestClassifier | class_weight=balanced_subsample;n_estimators=500 | pre>smote>clf | 42 | 5 |
| random_forest__sel-decided__imb-class_weight | sklearn.ensemble.RandomForestClassifier | class_weight=balanced_subsample;n_estimators=500 | pre>select>clf | 42 | 5 |
| random_forest__sel-decided__imb-smotenc | sklearn.ensemble.RandomForestClassifier | class_weight=balanced_subsample;n_estimators=500 | pre>select>smote>clf | 42 | 5 |
| hist_gb__sel-none__imb-class_weight | sklearn.ensemble.HistGradientBoostingClassifier | class_weight=balanced;learning_rate=0.1;max_leaf_nodes=31 | pre>clf | 42 | 5 |
| hist_gb__sel-decided__imb-class_weight | sklearn.ensemble.HistGradientBoostingClassifier | class_weight=balanced;learning_rate=0.1;max_leaf_nodes=31 | pre>select>clf | 42 | 5 |

Threshold-0.5 metrics (not the operating point; the deployed threshold is set in Milestone 6):

| variant | precision_at_threshold_mean | recall_at_threshold_mean | f1_at_threshold_mean | accuracy_at_threshold_mean | n_predicted_positive_at_threshold_mean |
|---|---|---|---|---|---|
| dummy__sel-none__imb-none | 0.0000 | 0.0000 | 0.0000 | 0.6787 | 0.0000 |
| logreg__sel-none__imb-class_weight | 0.6948 | 0.7503 | 0.7213 | 0.8138 | 245.6000 |
| logreg__sel-none__imb-smotenc | 0.7581 | 0.6720 | 0.7123 | 0.8257 | 201.6000 |
| logreg__sel-decided__imb-class_weight | 0.6791 | 0.7476 | 0.7115 | 0.8053 | 250.4000 |
| logreg__sel-decided__imb-smotenc | 0.6823 | 0.7414 | 0.7105 | 0.8059 | 247.2000 |
| random_forest__sel-none__imb-class_weight | 0.8038 | 0.5893 | 0.6796 | 0.8217 | 166.8000 |
| random_forest__sel-none__imb-smotenc | 0.7362 | 0.6685 | 0.7004 | 0.8163 | 206.6000 |
| random_forest__sel-decided__imb-class_weight | 0.7444 | 0.6175 | 0.6747 | 0.8090 | 188.6000 |
| random_forest__sel-decided__imb-smotenc | 0.6976 | 0.6632 | 0.6799 | 0.7994 | 216.2000 |
| hist_gb__sel-none__imb-class_weight | 0.7120 | 0.7318 | 0.7216 | 0.8186 | 233.8000 |
| hist_gb__sel-decided__imb-class_weight | 0.6868 | 0.7432 | 0.7136 | 0.8084 | 246.2000 |

## 3. Reading the ranking metrics honestly

Recall@K is close to **0.176** for every non-trivial model and Precision@K is above 0.95. This is a property
of the capacity assumption, not of the models: each validation fold holds about 227 dropouts but K
scales to 40 slots, so the ceiling on Recall@K is 40/227 ≈ 0.176. The models fill those slots
almost entirely with true dropouts. The dummy baseline reaches Recall@K 0.057 and
Precision@K 0.325 (the base rate), which is the reference the candidates must beat.
Recall at the 10-week window (`recall_at_k10w_mean`) shows how recall grows with capacity; Milestone 6
reports the full sensitivity and the business framing.

## 4. Imbalance treatment (research R-07 decision rule)

Rule: prefer class weighting unless SMOTENC improves mean PR-AUC by more than one fold standard deviation.

| model | pr_auc_class_weight | none | pr_auc_smotenc | delta_smotenc_minus_cw |
|---|---|---|---|---|
| dummy |  | 0.3213 |  |  |
| hist_gb | 0.8109 |  |  |  |
| logreg | 0.8182 |  | 0.8098 | -0.0083 |
| random_forest | 0.8070 |  | 0.8032 | -0.0038 |

Result: SMOTENC does **not** improve PR-AUC for either model (deltas negative), so the rule selects
**class weighting** for all candidates going forward. SMOTENC also costs runtime (LR ×49).

## 5. Effect of the Milestone 4 selection setting (embedded L1, k = 30)

| model | pr_auc_k30 | pr_auc_all_features | delta_k30_minus_all |
|---|---|---|---|
| dummy |  | 0.3213 |  |
| hist_gb | 0.8076 | 0.8109 | -0.0032 |
| logreg | 0.8111 | 0.8182 | -0.0070 |
| random_forest | 0.7823 | 0.8070 | -0.0247 |

Selection lowers PR-AUC for every candidate, most for the random forest, which prefers the full one-hot space.
Milestone 6 tunes each candidate in both settings and lets the selection matrix decide; the k = 30 subset
remains valuable for interpretability and is carried as a variant, not imposed.

## 6. Ablations (analysis only)

Promoted columns are **never** allowed for the deployed model. These runs quantify what the leakage guard
and the sensitive-attribute policy cost.

### 6.1 Ambiguous-timing financial columns (Debtor, Tuition fees up to date, Scholarship holder)

| model | columns_added | pr_auc_mean_without | pr_auc_mean_with | delta_pr_auc | recall_at_k_mean_without | recall_at_k_mean_with |
|---|---|---|---|---|---|---|
| logreg | 3 | 0.8182 | 0.8570 | 0.0389 | 0.1706 | 0.1724 |
| random_forest | 3 | 0.8070 | 0.8442 | 0.0372 | 0.1689 | 0.1733 |
| hist_gb | 3 | 0.8109 | 0.8471 | 0.0362 | 0.1733 | 0.1750 |

Including the three columns raises CV PR-AUC by roughly 0.036 to 0.039. This is precisely why they are
excluded: a status such as "tuition fees up to date" may be recorded after the student has already left, in
which case the gain is leakage, not foresight. They stay excluded until their recording time is verified
from the source article (open item in `data/README.md`). If verification shows they are known by the end of
the first semester, promoting them is a one-line change in `configs/features.yaml`.

### 6.2 Sensitive attributes (Gender, Age at enrollment, Nacionality, International, Marital status, Educational special needs)

| model | columns_added | pr_auc_mean_without | pr_auc_mean_with | delta_pr_auc | recall_at_k_mean_without | recall_at_k_mean_with |
|---|---|---|---|---|---|---|
| logreg | 6 | 0.8182 | 0.8201 | 0.0019 | 0.1706 | 0.1724 |
| random_forest | 6 | 0.8070 | 0.8136 | 0.0065 | 0.1689 | 0.1715 |
| hist_gb | 6 | 0.8109 | 0.8138 | 0.0029 | 0.1733 | 0.1733 |

Adding the six sensitive attributes changes PR-AUC by at most 0.0065 and Recall@K by at most
0.0026. The audit-only policy therefore costs almost nothing in validated performance, which
is the evidence PROJECT_DECISIONS asked for.

## 7. Calibration

Brier and ECE are reported per variant above; `cv_calibration.png` shows reliability curves from OOF scores.
Class-weighted models are known to over-predict the positive class, which appears as ECE values around
0.03 to 0.10. Whether to apply post-hoc calibration is decided in Milestone 6 (research R-10).

## 8. Limitations

- Fold-to-fold standard deviations (≈ 0.01 to 0.02 PR-AUC) are of the same order as several differences
  between candidates; rankings within that band are not decisive on this evidence alone.
- Candidates are untuned here (config defaults); Milestone 6 tunes hyperparameters under the same CV.
- The 0.5 threshold metrics are not an operating point for class-weighted models.
- Recall@K is capacity-bound (section 3); the illustrative K is a project assumption, not an institutional fact.
