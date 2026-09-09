# EDA + Feature Engineering Report

**Generated:** 2026-09-10 from the outputs of `python -m ssn data clean`, `data split`, and `eda`.
Every number cites a file under `reports/tables/`; nothing is typed from memory. Statistics use the
**training split only** (3539 records). Dataset: UCI 697, *Predict Students' Dropout and Academic
Success* (CC BY 4.0); provenance in `data/README.md`; profiling of the full raw file in
`reports/data_overview.md`.

**Scope of this milestone.** Cleaning, splitting, exploratory analysis, and stateless feature engineering.
No preprocessing was fitted, nothing was scaled across the dataset, no PCA, no resampling, no model. Any
statement about predictive value below is descriptive (a correlation or a rate difference), not a claim
about model performance.

## 1. Data-quality treatment (`clean_before_after.csv`)

| issue | column | count_before | count_after | treatment |
|---|---|---|---|---|
| header whitespace/BOM | <all> | 0 | 0 | stripped on load (schema.load_raw) |
| exact duplicate rows | <all> | 0 | 0 | drop, keep first |
| undocumented Target label | Target | 0 | 0 | drop row |
| rows with any missing value | <all> | 0 | 0 | drop row (UCI: no missing values) |
| approved > enrolled (1st sem) | Curricular units 1st sem (approved) | 0 | 0 | flag only; none expected |
| zero units enrolled (1st sem) | Curricular units 1st sem (enrolled) | 180 | 180 | keep; rate features become NaN for these rows (imputed inside CV later) |
| grade == 0 (1st sem) | Curricular units 1st sem (grade) | 718 | 718 | keep; coincides with zero approvals, a real academic state not an error |
| IQR outlier candidates | <numeric> | -1 | -1 | keep all; see reports/tables/profile_outliers.csv; tree models are robust, LR gets scaling in-pipeline |
| rows | <all> | 4424 | 4424 | net effect of all treatments |

**Decisions.** The raw file has no missing values, no duplicate rows, and no values outside the UCI
documented codes or ranges (`reports/data_overview.md`, sections 5 to 7), so no row was altered or
removed. Two academic states are kept deliberately: 180
students with zero first-semester units enrolled (their rate features are undefined and become NaN), and
718 students with a first-semester grade of 0,
every one of whom also has zero approvals; these are real outcomes, not errors. IQR outlier candidates
(`profile_outliers.csv`) are kept: tree models are insensitive to them and logistic regression receives
scaling inside the cross-validation pipeline in Milestone 4, never here.

## 2. Class imbalance (`split_summary.csv`, `profile_target.csv`)

| split | n | n_dropout | positive_rate |
|---|---|---|---|
| train | 3539 | 1137 | 0.3213 |
| test | 885 | 284 | 0.3209 |
| demo_cohort (=test features only) | 885 |  |  |

Full file: Graduate 2209, Dropout 1421,
Enrolled 794. The binary target (`is_dropout` = 1 for Dropout only) has a
positive rate of **0.3213** in train and 0.3209 in test after stratified splitting (seed 42,
80/20, matching the UCI recommended split). Treatment of the imbalance is a modelling decision deferred to
Milestone 5, where class weighting and SMOTENC are compared under cross-validation; the PR-AUC primary metric
was chosen because of this imbalance (spec FR-012).

## 3. Feature-availability list (`configs/features.yaml`)

The deployed model may use only `enrollment` and `first_semester` columns with role `feature`. Sensitive
attributes are audit-only. Second-semester columns describe the period after the prediction point.
Financial-status columns have undocumented timing and are excluded by default (open item in `data/README.md`).

| availability | role | n |
|---|---|---|
| ambiguous | feature | 3 |
| enrollment | feature | 15 |
| enrollment | sensitive | 6 |
| first_semester | feature | 6 |
| outcome | target | 1 |
| second_semester | feature | 6 |

Excluded from model inputs (16 columns):

| column | availability | role |
|---|---|---|
| Marital status | enrollment | sensitive |
| Nacionality | enrollment | sensitive |
| Educational special needs | enrollment | sensitive |
| Debtor | ambiguous | feature |
| Tuition fees up to date | ambiguous | feature |
| Gender | enrollment | sensitive |
| Scholarship holder | ambiguous | feature |
| Age at enrollment | enrollment | sensitive |
| International | enrollment | sensitive |
| Curricular units 2nd sem (credited) | second_semester | feature |
| Curricular units 2nd sem (enrolled) | second_semester | feature |
| Curricular units 2nd sem (evaluations) | second_semester | feature |
| Curricular units 2nd sem (approved) | second_semester | feature |
| Curricular units 2nd sem (grade) | second_semester | feature |
| Curricular units 2nd sem (without evaluations) | second_semester | feature |
| Target | outcome | target |

## 4. Engineered first-semester features (`src/ssn/features/engineering.py`)

Stateless and row-wise; every input is allow-listed (enforced by `tests/unit/test_engineering.py`).

| feature | inputs | rationale |
|---|---|---|
| sem1_approval_rate | Curricular units 1st sem (approved), Curricular units 1st sem (enrolled) | Share of enrolled first-semester units passed: the most direct early signal of academic progress. |
| sem1_evaluation_participation_rate | Curricular units 1st sem (evaluations), Curricular units 1st sem (enrolled) | Evaluations sat per enrolled unit: engagement with assessment, distinct from passing. |
| sem1_non_evaluation_rate | Curricular units 1st sem (without evaluations), Curricular units 1st sem (enrolled) | Share of enrolled units with no evaluation at all: a disengagement or withdrawal signal. |
| grade_diff_vs_admission | Curricular units 1st sem (grade), Admission grade | First-semester grade (0-20 scale, rescaled to 0-200) minus admission grade (0-200): change in performance relative to entry level. |
| sem1_credited_share | Curricular units 1st sem (credited), Curricular units 1st sem (enrolled) | Share of enrolled units credited from prior study: workload actually taken is lower. |
| sem1_load | Curricular units 1st sem (enrolled) | Number of first-semester units enrolled: workload proxy (kept explicit for interpretability). |
| sem1_any_approved | Curricular units 1st sem (approved) | Whether at least one unit was passed: separates zero-progress students from the rest. |

**Zero denominators (`zero_denominators.csv`).** 138 training records have zero units
enrolled, so the four rate features are NaN for them. They are imputed by the median inside the CV pipeline
(Milestone 4); no imputation statistic is computed in this milestone. `grade_diff_vs_admission` rescales the
first-semester grade (0-20) by 10 to the admission-grade scale (0-200), both per UCI documentation.

`age_band` is also produced but is **audit-only**: it derives from a sensitive column and is never a model
input.

## 5. Distributions by outcome (`eda_numeric_summary_by_target.csv`)

Figures: `eda_numeric_source_by_target.png`, `eda_engineered_by_target.png`.

| feature | mean_non_dropout | mean_dropout | difference |
|---|---|---|---|
| grade_diff_vs_admission | -5.737 | -51.54 | -45.8 |
| Curricular units 1st sem (grade) | 12.23 | 7.354 | -4.877 |
| Curricular units 1st sem (approved) | 5.719 | 2.607 | -3.112 |
| Admission grade | 128 | 125.1 | -2.973 |
| Previous qualification (grade) | 133.3 | 131.1 | -2.226 |
| Curricular units 1st sem (evaluations) | 8.535 | 7.857 | -0.6771 |
| Curricular units 1st sem (enrolled) | 6.469 | 5.914 | -0.5554 |
| sem1_load | 6.469 | 5.914 | -0.5554 |
| sem1_approval_rate | 0.877 | 0.4096 | -0.4674 |
| sem1_any_approved | 0.9496 | 0.6069 | -0.3427 |
| GDP | 0.1014 | -0.128 | -0.2294 |
| Application order | 1.784 | 1.618 | -0.1652 |
| Curricular units 1st sem (credited) | 0.7585 | 0.6236 | -0.1349 |
| sem1_credited_share | 0.0687 | 0.0641 | -0.0046 |
| sem1_evaluation_participation_rate | 1.345 | 1.342 | -0.0022 |
| sem1_non_evaluation_rate | 0.0149 | 0.0379 | 0.023 |
| Inflation rate | 1.224 | 1.281 | 0.0574 |
| Unemployment rate | 11.53 | 11.6 | 0.0643 |
| Curricular units 1st sem (without evaluations) | 0.1028 | 0.2093 | 0.1065 |

## 6. Categorical features: dropout rate by category (`eda_dropout_rate_by_category.csv`)

Figure: `eda_dropout_rate_by_category.png`. Groups with fewer than 30 training records are
excluded from the figure and marked `reliable = False` in the table. Highest observed rates among reliable groups:

| column | code | label | n | dropout_rate |
|---|---|---|---|---|
| Mother's qualification | 34 | Unknown | 98 | 0.7959 |
| Father's qualification | 34 | Unknown | 86 | 0.7907 |
| Mother's occupation | 90 | Other Situation | 61 | 0.7541 |
| Father's occupation | 90 | Other Situation | 50 | 0.74 |
| Mother's occupation | 0 | Student | 111 | 0.7387 |
| Previous qualification | 19 | Basic education 3rd cycle (9th/10th/11th year) or equiv. | 123 | 0.6748 |
| Father's occupation | 0 | Student | 95 | 0.6737 |
| Previous qualification | 12 | Other - 11th year of schooling | 37 | 0.6216 |
| Previous qualification | 3 | Higher education - degree | 108 | 0.6204 |
| Application mode | 7 | Holders of other higher courses | 118 | 0.6186 |

Overall training dropout rate for reference: 0.3213.

## 7. Correlations with the target (`eda_spearman_with_target.csv`)

Figure: `eda_correlation_spearman.png` (Spearman, allowed numeric + engineered features).

| Most negative with is_dropout | rho | Most positive with is_dropout | rho |
|---|---|---|---|
| sem1_approval_rate | -0.590 | sem1_non_evaluation_rate | 0.084 |
| Curricular units 1st sem (approved) | -0.514 | Curricular units 1st sem (without evaluations) | 0.081 |
| Curricular units 1st sem (grade) | -0.437 | sem1_evaluation_participation_rate | 0.048 |
| sem1_any_approved | -0.436 | Inflation rate | 0.015 |
| grade_diff_vs_admission | -0.357 | Unemployment rate | 0.007 |
| Curricular units 1st sem (enrolled) | -0.165 | sem1_credited_share | -0.005 |

These are descriptive associations on the training split, not measures of model performance. The
first-semester approval and grade signals dominate, which is consistent with the academic-progress
rationale for the engineered features.

## 8. Sensitive-group distributions (`eda_dropout_rate_by_sensitive_group.csv`, `eda_age_band_counts.csv`)

Figure: `eda_sensitive_groups.png`. Aggregate context for the Milestone 7 fairness audit; these columns are
not model inputs. Reliable groups (n ≥ min_group_size):

| attribute | group | label | n | share | dropout_rate |
|---|---|---|---|---|---|
| Educational special needs | 0.0 | no | 3499 | 0.9887 | 0.3218 |
| Educational special needs | 1.0 | yes | 40 | 0.0113 | 0.275 |
| Gender | 0.0 | female | 2293 | 0.6479 | 0.2525 |
| Gender | 1.0 | male | 1246 | 0.3521 | 0.4478 |
| International | 0.0 | no | 3452 | 0.9754 | 0.3227 |
| International | 1.0 | yes | 87 | 0.0246 | 0.2644 |
| Marital status | 1.0 | single | 3127 | 0.8836 | 0.3006 |
| Marital status | 2.0 | married | 306 | 0.0865 | 0.4641 |
| Marital status | 4.0 | divorced | 72 | 0.0203 | 0.5417 |
| Nacionality | 1.0 | Portuguese | 3452 | 0.9754 | 0.3227 |
| age_band | 17-19 |  | 1549 | 0.4377 | 0.2137 |
| age_band | 20-24 |  | 1078 | 0.3046 | 0.2801 |
| age_band | 25-34 |  | 556 | 0.1571 | 0.5558 |
| age_band | 35+ |  | 356 | 0.1006 | 0.5478 |

Nationality has 20 observed groups, all but Portuguese below the reliable size;
the fairness audit will report them with subgroup-size warnings or suppress them (spec FR-047).

### Age bands (PV-06 decision)

Training age distribution (`eda_age_summary.csv`): min 17, p25 19, median 20,
p75 25, p90 35, max 70. Three candidate schemes were compared
(`eda_age_band_alternatives.csv`); scheme A was chosen because its cut points sit on the observed quartiles
(19 and 25) and on the conventional traditional-age / mature-student boundary, and every band exceeds the
minimum group size. Recorded in `configs/base.yaml` under `fairness.age_bands`.

| age_band | n | dropout_rate |
|---|---|---|
| 17-19 | 1549 | 0.2137 |
| 20-24 | 1078 | 0.2801 |
| 25-34 | 556 | 0.5558 |
| 35+ | 356 | 0.5478 |

## 9. Analysis-only view of second-semester columns

`analysis_only_second_semester_distributions.png` plots the six second-semester columns from the raw file
by source Target, to document why they are prohibited: they describe the period after the end-of-first-
semester prediction point. They are excluded by `configs/features.yaml`, by `project_for_model`, and by
`tests/unit/test_engineering.py`.

## 10. Unresolved items carried forward

- Recording time of Debtor, Tuition fees up to date, Scholarship holder (see `data/README.md`); ablation
  planned in Milestone 5.
- Mother's and Father's qualification and occupation are socioeconomic proxies kept as features per
  PROJECT_DECISIONS; the fairness audit and limitations section must discuss proxy risk.
- Imbalance treatment and imputation strategy are decided in Milestones 4 and 5 under cross-validation.

## 11. Feature selection and dimensionality reduction (Milestone 4, computed 2026-09-10)

Source files: `selection_cv_by_k.csv`, `selection_filter_scores.csv`, `selection_embedded_scores.csv`,
`selection_decision.json`, `pca_explained_variance.csv`, `pca_vs_nopca_cv.csv`; figures `pca_scree.png`,
`pca_2d_train.png`; notebook `notebooks/03_feature_selection_pca.ipynb`.

### 11.1 Design

- **Data:** training split only (3539 records). The held-out test split was not opened by
  any command in this milestone (enforced by `tests/unit/test_selection_in_pipeline.py` and
  `tests/unit/test_pca_fit_isolation.py`, which spy on every parquet read).
- **Validation:** 5-fold stratified cross-validation, seed 42. Preprocessing (median imputation,
  scaling, one-hot encoding), the selector, and PCA are all pipeline steps, so each is fitted on the
  training folds only. After preprocessing the feature space has **207** columns (19 numeric incl. 7
  engineered, 2 binary, 186 one-hot categorical).
- **Reference estimator:** class-weighted logistic regression, chosen because it is fast and neutral; its
  scores compare selector *settings*, not models. No candidate-model ranking is made here.
- **Selectors:** filter = `SelectKBest` with mutual information; embedded = `SelectFromModel` over an
  L1-penalised logistic regression (coefficients ranked by magnitude). Grid k = [10, 20, 30, 50, 80, 'all'].
- **Decision rule:** smallest k whose mean CV PR-AUC is within 1.0 standard deviation of the best
  setting (ties: filter before embedded).

### 11.2 Cross-validation over the k grid

| kind | method | k | pr_auc_mean | pr_auc_std | roc_auc_mean | roc_auc_std |
|---|---|---|---|---|---|---|
| filter | mutual_info | 10 | 0.7789 | 0.0117 | 0.8494 | 0.0116 |
| filter | mutual_info | 20 | 0.7925 | 0.0125 | 0.8563 | 0.0109 |
| filter | mutual_info | 30 | 0.8011 | 0.0110 | 0.8625 | 0.0106 |
| filter | mutual_info | 50 | 0.8038 | 0.0118 | 0.8635 | 0.0105 |
| filter | mutual_info | 80 | 0.8120 | 0.0132 | 0.8714 | 0.0123 |
| filter | mutual_info | all | 0.8180 | 0.0165 | 0.8778 | 0.0124 |
| embedded | l1_logreg | 10 | 0.7528 | 0.0374 | 0.8425 | 0.0256 |
| embedded | l1_logreg | 20 | 0.8000 | 0.0146 | 0.8681 | 0.0110 |
| embedded | l1_logreg | 30 | 0.8111 | 0.0174 | 0.8730 | 0.0121 |
| embedded | l1_logreg | 50 | 0.8150 | 0.0163 | 0.8756 | 0.0117 |
| embedded | l1_logreg | 80 | 0.8175 | 0.0159 | 0.8765 | 0.0136 |
| embedded | l1_logreg | all | 0.8180 | 0.0165 | 0.8778 | 0.0124 |

**Decision (`selection_decision.json`):** `embedded` / `l1_logreg`, **k = 30** (CV PR-AUC 0.8111 ± 0.0174;
best setting 0.818 at k = all). Keeping all 207 features scores highest on average, but the
gain over 30 embedded-selected features is smaller than one fold-to-fold standard deviation, so the parsimony
rule prefers the smaller, more interpretable set. This becomes the `use_selection` setting for candidate
pipelines in Milestone 5, where each candidate is compared with and without it.

### 11.3 What the selectors rank highly (training split, descriptive)

Embedded L1 ranking, top 30, by original column: Course (8), Mother's occupation (6), Application mode (4), Father's occupation (3), Mother's qualification (2), Curricular units 1st sem (approved) (1), sem1_any_approved (1), sem1_approval_rate (1), Curricular units 1st sem (grade) (1), Curricular units 1st sem (credited) (1), sem1_evaluation_participation_rate (1), Previous qualification (1).
Filter (mutual information) ranking, top 30, by original column: Father's occupation (4), Father's qualification (4), Mother's occupation (4), Application mode (3), Previous qualification (2), sem1_approval_rate (1), Curricular units 1st sem (approved) (1), Curricular units 1st sem (grade) (1), grade_diff_vs_admission (1), sem1_any_approved (1), sem1_evaluation_participation_rate (1), Curricular units 1st sem (evaluations) (1), Previous qualification (grade) (1), sem1_load (1), Curricular units 1st sem (enrolled) (1), Admission grade (1), GDP (1), Mother's qualification (1).

Embedded features selected in at least 80% of folds (top-20 setting):

| feature | score | selected_frequency_top20 | source_column |
|---|---|---|---|
| cat__Mother's occupation_191 | 1.7029 | 1.0000 | Mother's occupation |
| num__Curricular units 1st sem (approved) | 1.5096 | 1.0000 | Curricular units 1st sem (approved) |
| cat__Mother's occupation_0 | 1.4114 | 1.0000 | Mother's occupation |
| cat__Mother's qualification_4 | 1.3666 | 1.0000 | Mother's qualification |
| cat__Course_9130 | 1.2063 | 1.0000 | Course |
| cat__Course_9853 | 1.0687 | 1.0000 | Course |
| cat__Father's occupation_90 | 1.0502 | 0.8000 | Father's occupation |
| cat__Course_8014 | 0.8816 | 1.0000 | Course |
| cat__Application mode_7 | 0.8577 | 0.8000 | Application mode |
| cat__Mother's qualification_34 | 0.8436 | 1.0000 | Mother's qualification |
| num__sem1_any_approved | 0.8229 | 1.0000 | sem1_any_approved |
| num__sem1_approval_rate | 0.7658 | 1.0000 | sem1_approval_rate |
| cat__Course_9238 | 0.7321 | 1.0000 | Course |
| cat__Application mode_39 | 0.6849 | 1.0000 | Application mode |
| num__Curricular units 1st sem (grade) | 0.6845 | 1.0000 | Curricular units 1st sem (grade) |

The two methods agree on the academic core: first-semester approvals, approval rate, first-semester grade,
`sem1_any_approved`, and grade change versus admission. They disagree on the tails: the L1 ranking gives large
coefficients to sparse one-hot indicators (individual parental-occupation and course codes), which the
mutual-information ranking does not reward. This is a known behaviour of L1 on rare indicators and is one
reason the CV table, not the raw ranking, drives the decision.

### 11.4 PCA

Purpose: (a) describe how concentrated the variance of the preprocessed feature space is, (b) provide a 2-D
projection for visualisation, and (c) test whether replacing the features with principal components helps
the reference estimator. It is **not** used to select features.

- **42** of 207 components are needed to reach 95% of the variance (`pca_scree.png`). The first two
  components explain 23.3% and 12.0%; the 2-D projection (`pca_2d_train.png`) shows
  overlapping classes with only partial separation.

| pipeline | pr_auc_mean | pr_auc_std | roc_auc_mean | roc_auc_std |
|---|---|---|---|---|
| no_pca | 0.8180 | 0.0165 | 0.8778 | 0.0124 |
| pca_0.95_variance | 0.8007 | 0.0104 | 0.8670 | 0.0096 |
| pca_2_components | 0.7298 | 0.0248 | 0.8289 | 0.0104 |

**Decision:** PCA is retained for analysis and visualisation only. Under identical CV, the 95%-variance PCA
pipeline scores 0.8007 PR-AUC versus 0.8180 without PCA, and the two-component pipeline 0.7298.
Candidate pipelines in Milestone 5 therefore use the original (optionally selected) features
(`use_pca: false`), which also keeps SHAP explanations in terms of named features.

### 11.5 Limitations of this analysis

- Variance concentration is dominated by 186 one-hot indicator columns, each carrying little variance; PCA on
  a mixed one-hot/numeric space is a descriptive device here, not a modelling recommendation.
- Rankings are specific to the reference estimator; tree-based candidates may weight features differently.
  The Milestone 5 comparison runs each candidate with and without the selected subset.
- L1 coefficients on rare indicators can be unstable across folds; the stability column and the CV table
  are reported for that reason.
- Several highly ranked indicators are parental-occupation and parental-qualification codes, i.e.
  socioeconomic proxies kept as features by PROJECT_DECISIONS. Their prominence must be discussed in the
  fairness audit and limitations (Milestone 7).
- The parsimony rule is a project convention (one CV standard deviation); a different tolerance would
  change k. It is recorded in `configs/base.yaml` so the choice is auditable.
