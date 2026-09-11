# Final Report — Fair and Explainable Student Dropout Risk Prediction for Early Academic Support

**Companion application:** Student Success Navigator · **Model version:** 1.0.0 · **Date:** 2026-09-10
**Repository:** https://github.com/joopabs/student-success-navigator · **Author:** Julius Pabular

> Every figure in this report is read from a file produced by the pipeline (paths in each section). Capacity, window,
> and "share of dropouts reached" figures are ILLUSTRATIVE assumptions; all metrics are MEASURED. The system suggests a
> short outreach list for adviser review; it does not predict any student's future with certainty, does not replace
> advisers, is not shown to cause better outcomes, and can make no adverse decision.

## Contents

1. Problem understanding and framing · 2. Data collection and understanding · 3. Preprocessing, EDA and feature
engineering · 4. Model implementation and comparison · 5. Critical thinking, ethical AI and bias auditing (includes the
Bias & Fairness Analysis) · 6. Presentations · 7. Repository and reproducibility · 8. Optional steps · 9. Limitations ·
10. Rubric map

## 1. Problem understanding and framing

**Business problem.** Students who leave a programme early are a loss for them and for the institution. Advisers can
support at-risk students, but adviser time is limited and there is no consistent, explainable way to decide whom to
contact first at the moment when it matters: the end of the first semester.

**Data-science problem.** Binary classification. Unit of analysis: one student enrollment record. Prediction point: end
of the first semester. Target `is_dropout` = 1 where the source Target is Dropout, 0 for Enrolled or Graduate
(`PROJECT_DECISIONS.md`). The output is a *support-priority score* used to rank students for voluntary, supportive
adviser outreach.

**Intended use and non-use.** Decision support for qualified advisers and student-support teams, with human review of
every record. Prohibited: any automated or adverse decision about admission, enrollment, scholarships, financial aid,
grades, discipline, housing, or other opportunities (`.specify/memory/constitution.md`, Principle XI).

**Metrics.** Primary technical metric: PR-AUC, chosen because the positive class is a minority (positive rate
0.321). Intervention metric: Recall@K and Precision@K, where K is the outreach capacity.
Secondary: ROC-AUC, Brier score, expected calibration error, precision/recall/F1 and confusion matrices at the operating
threshold, group-level fairness metrics. **Business KPI (illustrative):** the share of eventual dropouts reached within a
fixed outreach capacity. The capacity is an assumption, 10 conversations per week over
5 weeks (K = 50 per cohort of 885), stored in `configs/base.yaml` with
an `illustrative: true` flag that the code refuses to run without. No cost or return figure is asserted because the data
contain none.

**Governance.** The project is governed by a written constitution (12 principles, 10 quality gates) and a Spec Kit
specification, plan, research log, contracts, and 92-task checklist under `specs/001-dropout-risk-navigator/`.

## 2. Data collection and understanding

**Source.** UCI Machine Learning Repository dataset 697, *Predict Students' Dropout and Academic Success*, Realinho,
Vieira Martins, Machado and Baptista (2021), DOI 10.24432/C5MC89, licence CC BY 4.0. One Portuguese higher-education
institution. Full citation, licence verification checklist, checksum, and download procedure: `data/README.md`. The
data are **not** representative of Philippine or other institutions.

**Observed facts** (`reports/data_overview.md`, `reports/tables/profile_*.csv`): 4424 records × 37 columns; 0 missing
cells; 0 duplicate rows; 0 values outside the documented codes and ranges. Target: Graduate 2209,
Dropout 1421, Enrolled 794; derived `is_dropout` positive rate 0.3212.

**Data dictionary.** `data/data_dictionary.md` lists every column with type, availability time (enrollment, first
semester, second semester, outcome, ambiguous), role, documented codes or ranges, observed values, and an
encoding-verification flag. All 22 coded columns have every observed code inside the UCI documentation, including
Gender (1 = male, 0 = female), which the fairness audit requires before it will run.

**Column classification** (`configs/features.yaml`): 21 allowed model inputs (15 enrollment-time, 6 first-semester);
6 sensitive attributes, audit-only (gender, age at enrollment, nationality, international status, marital status,
educational special needs); 3 financial-status columns with undocumented recording time, excluded by default (Debtor,
Tuition fees up to date, Scholarship holder); 6 second-semester columns, prohibited; 1 target. Open verification item:
the source article could not be retrieved programmatically to settle the timing of the three financial columns.

## 3. Data preprocessing, EDA and feature engineering

Full report: `reports/eda_feature_engineering_report.md` (sections 1–12); notebooks 02 and 03.

**Cleaning** (`clean_before_after.csv`). Every treatment is logged with before/after counts. No row was altered or
removed. Kept deliberately: 180 students with zero first-semester units enrolled and
718 with a first-semester grade of 0 (all with zero approvals): real academic states, not errors. IQR outlier
candidates are kept; tree models are insensitive and logistic regression is scaled inside the pipeline.

**Split** (`split_summary.csv`). Stratified 80/20, seed 42: train 3539 (positive rate 0.3213),
test 885 (positive rate 0.3209). The test split doubles as the de-identified demo cohort
for the app (features only, synthetic ids); its labels and sensitive columns live in an evaluator-only file the app never reads.

**Applied EDA** (`reports/figures/eda_*.png`, training split only). First-semester approvals, approval rate and grade show
the strongest Spearman associations with dropout; categorical dropout rates by programme and application route are
reported for groups above the minimum size; sensitive-group base rates are reported as audit context (e.g. dropout
rate by gender and age band) but never used as inputs. Second-semester distributions are plotted analysis-only.

**Feature engineering** (`src/ssn/features/engineering.py`). Seven stateless features from allow-listed inputs, each
with an academic rationale: first-semester approval rate, evaluation participation rate, non-evaluation rate, grade
change versus admission grade (0–20 rescaled to 0–200), credited share, load, any-approved. 138 training
records have zero enrolled units, so rate features are NaN and are median-imputed inside the cross-validation pipeline.
`age_band` is derived for auditing only and is never a model input.

**Leakage controls, measured.** Preprocessing, selectors, PCA and estimators are pipeline steps fitted inside folds;
tests spy on every parquet read to prove the test split is never opened before the single evaluation. Including the
three ambiguous financial columns would raise CV PR-AUC by 0.036 to 0.039 (`ablation_ambiguous.csv`), a gain
that may be leakage, so they stay excluded. Excluding the six sensitive attributes costs at most 0.0065
(`ablation_sensitive.csv`).

**Feature selection** (`selection_cv_by_k.csv`, `selection_decision.json`). Filter (mutual information) and embedded
(L1 logistic) selectors as pipeline steps over k ∈ [10, 20, 30, 50, 80, 'all'] of 207 preprocessed columns; reference
estimator class-weighted logistic regression. Best mean PR-AUC 0.8180 at k = all; the parsimony rule (within one CV
std) chose embedded k = 30 (0.8111). Both agree on the academic core; L1 also rewards sparse parental-background
indicators, a proxy concern carried to section 5.

**Dimensionality reduction** (`pca_explained_variance.csv`, `pca_vs_nopca_cv.csv`). 42 components reach 95% variance.
Under identical CV the PCA pipeline scores 0.8007 PR-AUC versus 0.8180 without, so PCA is retained for
analysis and visualisation only.

## 4. Model implementation and comparison

Reports: `reports/model_comparison_cv.md`, `reports/model_selection_and_evaluation.md`; notebook 04.

**Candidates and validation.** DummyClassifier (prior) baseline; class-weighted logistic regression; random forest
(500 trees); HistGradientBoosting. Five-fold stratified CV on the training split, seed 42, with selection (none /
embedded k = 30) and imbalance (class weighting / SMOTENC) variants: 11 pipelines, each with runtime, seed, estimator
and parameters recorded (`cv_comparison.csv`).

| model | pr_auc_mean | pr_auc_std | roc_auc_mean | recall_at_k_mean | precision_at_k_mean | brier_mean | ece_mean | fit_time_s_mean |
|---|---|---|---|---|---|---|---|---|
| dummy | 0.3213 | 0.0007 | 0.5000 | 0.0572 | 0.3250 | 0.2181 | 0.0008 | 0.0211 |
| logreg | 0.8182 | 0.0166 | 0.8777 | 0.1706 | 0.9700 | 0.1344 | 0.0961 | 0.0313 |
| random_forest | 0.8070 | 0.0094 | 0.8724 | 0.1689 | 0.9600 | 0.1260 | 0.0321 | 1.1448 |
| hist_gb | 0.8109 | 0.0144 | 0.8694 | 0.1733 | 0.9850 | 0.1316 | 0.0667 | 0.5286 |

SMOTENC lowered PR-AUC for both models it was tried on, so class weighting is used. Recall@K is capacity-bound: each
fold holds about 227 dropouts but K scales to 40 slots, a ceiling of about 0.176.

**Tuning** (`tuned_params.json`, `tuning_results_*.csv`). RandomizedSearchCV with PR-AUC scoring on the training split,
each candidate in both selection settings. Tuned PR-AUC ranged from 0.8057 to 0.8186, all within one CV
standard deviation.

**Selection** (`selection_matrix_ranked.csv`, `model_selection_decision.json`). Criteria: PR-AUC, Recall@K,
Precision@K, Brier, ECE, preliminary fairness (max demographic-parity difference, min disparate-impact ratio),
native SHAP support, maintainability, fit time. Accuracy excluded. Rule: 1) eligible = candidates whose OOF PR-AUC >= best PR-AUC - 1 x CV std of the best; 2) rank eligible by Recall@K (rounded to 3 dp, desc), then ECE (2 dp, asc), then fairness_max_dp_difference (2 dp, asc), then Brier (3 dp, asc), then OOF fit time (asc). Accuracy is not a criterion (constitution VIII). Explainability must be natively SHAP-supported.

| rank | candidate | pr_auc | recall_at_k | ece | fairness_max_dp_difference | brier |
|---|---|---|---|---|---|---|
| 1 | random_forest__sel-none | 0.8078 | 0.1715 | 0.0539 | 0.1107 | 0.1286 |
| 2 | hist_gb__sel-none | 0.8121 | 0.1724 | 0.0761 | 0.0812 | 0.1320 |
| 3 | logreg__sel-none | 0.8173 | 0.1706 | 0.0938 | 0.1309 | 0.1343 |
| 4 | random_forest__sel-decided | 0.8066 | 0.1706 | 0.0895 | 0.1297 | 0.1355 |
| 5 | logreg__sel-decided | 0.8103 | 0.1706 | 0.0955 | 0.1262 | 0.1370 |
| 6 | hist_gb__sel-decided | 0.8029 | 0.1697 | 0.0885 | 0.0974 | 0.1379 |

**Chosen:** `random_forest__sel-none`. The three families are indistinguishable on PR-AUC; the rule falls through to a Recall@K tie
and then to calibration error, where the random forest is clearly best. **Calibration:** isotonic, applied under the
documented rule (ECE 0.054 → 0.017, Brier 0.1286 → 0.1251, PR-AUC unchanged within noise).

**Threshold and bands** (`threshold_and_bands.json`, `threshold_tradeoffs.csv`). Threshold 0.9728 is the OOF score at
the capacity selection rate (200 of 3539). Alternatives and their false-positive / false-negative trade-offs:

| rule | threshold | n_selected | precision | recall | false_positives | false_negatives |
|---|---|---|---|---|---|---|
| capacity (chosen) | 0.9728 | 202 | 0.9703 | 0.1724 | 6 | 941 |
| f1_optimal | 0.3848 | 1154 | 0.7106 | 0.7212 | 334 | 317 |
| precision>=0.8 | 0.5355 | 861 | 0.8002 | 0.6060 | 172 | 448 |
| 0.5 (default) | 0.5000 | 922 | 0.7874 | 0.6385 | 196 | 411 |

Three supportive bands (Priority outreach, Check-in suggested, Standard support) are stored in the manifest.

**Reproducibility and artifacts.** `models/final_pipeline.joblib` (regenerated with `make final`) and
`models/manifest.json` (git SHA, config hash, pipeline SHA-256, library versions, seed, exact 21-column input schema,
threshold, bands, CV summary, test counter). A fresh-environment re-run reproduced every compared table with a
maximum absolute delta of 0 (`docs/REPRODUCIBILITY.md`).

**Single held-out evaluation** (`test_metrics_all_models.csv`; `test_evaluations` = 1):

| model | pr_auc | roc_auc | recall_at_k | precision_at_k | brier | ece |
|---|---|---|---|---|---|---|
| final | 0.8175 | 0.8919 | 0.1690 | 0.9600 | 0.1180 | 0.0336 |
| hist_gb__sel-none | 0.8174 | 0.8783 | 0.1761 | 1.0000 | 0.1309 | 0.0849 |
| random_forest__sel-decided | 0.8163 | 0.8871 | 0.1761 | 1.0000 | 0.1321 | 0.0983 |
| random_forest__sel-none | 0.8161 | 0.8915 | 0.1690 | 0.9600 | 0.1235 | 0.0754 |
| logreg__sel-none | 0.8154 | 0.8775 | 0.1761 | 1.0000 | 0.1373 | 0.1014 |
| hist_gb__sel-decided | 0.8103 | 0.8778 | 0.1761 | 1.0000 | 0.1354 | 0.0930 |
| logreg__sel-decided | 0.8050 | 0.8750 | 0.1761 | 1.0000 | 0.1382 | 0.1033 |
| dummy | 0.3209 | 0.5000 | 0.0739 | 0.4200 | 0.2179 | 0.0004 |

Final model: PR-AUC 0.8175 (CV estimate 0.8078), ROC-AUC 0.8919, Brier 0.1180, ECE 0.0336; at the threshold it selects
57 of 885 students with precision 0.965. Illustrative KPI: under the stated assumption, a
5-week window reaches a measured 16.9% of the 284 eventual dropouts in the test cohort with
96% precision; a 10-week window reaches 32.7% (`test_recall_precision_at_k.csv`).

## 5. Critical thinking, ethical AI and bias auditing

### 5.1 Explainability

Method (`reports/explainability/method.json`): shap.TreeExplainer on each of the 5 calibrated ensemble members;
one-hot columns summed per source feature and averaged across members; explanations describe uncalibrated base-estimator
contributions, not the calibrated probability. Global importance (`shap_global_importance.csv`, `shap_global_bar.png`):

| feature | mean_abs_shap | mean_signed_shap | engineered |
|---|---|---|---|
| sem1_approval_rate | 0.0919 | -0.0185 | True |
| Curricular units 1st sem (approved) | 0.0667 | -0.0122 | False |
| Curricular units 1st sem (grade) | 0.0371 | -0.0115 | False |
| grade_diff_vs_admission | 0.0305 | -0.0095 | True |
| Application mode | 0.0253 | -0.0066 | False |
| sem1_any_approved | 0.0245 | -0.0090 | True |
| Course | 0.0201 | -0.0050 | False |
| Curricular units 1st sem (evaluations) | 0.0107 | -0.0049 | False |
| sem1_evaluation_participation_rate | 0.0107 | -0.0053 | True |
| Previous qualification | 0.0105 | -0.0028 | False |

Representative true-positive, false-positive, false-negative and true-negative records (synthetic ids,
`shap_local_examples.json`) are rendered into supportive adviser phrases through `configs/language.yaml`; a test proves
no sensitive attribute can appear. PDP and ICE plots cover 9 continuous raw features; engineered features are
excluded from PDP with the reason recorded (they cannot be varied independently inside the pipeline).

### 5.2 Limitations (`reports/limitations.md`)

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

**Ranking resolution at the top of the list.** The score saturates on the most clear-cut records: 21 of the 885 held-out
records tie at exactly 1.00 and 42 sit at or above 0.99, so order inside that block is settled by the record-id
tie-break rather than by the model. Every one of the 50 records in the default list passed zero first-semester units and
has a first-semester grade average of zero, which makes their SHAP explanations effectively identical: all 50 show the
same two leading factors, and only two distinct top-five sequences occur across them. Advisers should read the top block
as an unordered set of comparably placed records, not as a strict order of priority. The model is still doing more than
the bare rule would: 150 records in the cohort passed no units and 82% of those later left, while the model's top 50
reaches 96%, so it is ranking within that group on secondary features (units enrolled, admission grade, application
route). But SHAP attributes most of the magnitude to the zero-unit features, so the signal separating those 50 from the
other 100 sits below the factors an adviser is shown; showing more factors per record would not surface it, because the
useful contrast is between records and the per-record view does not present one.

**Human oversight.** The tool proposes a short outreach list; a qualified adviser reviews each record, may dismiss or
override any suggestion, and records the decision locally. No automated or adverse decision is made or recommended.
Advisers should keep independent referral routes, especially for first-year students where model recall is lowest, and
the Equity Dashboard should be reviewed each outreach cycle.

### 5.3 Bias & Fairness Analysis (`reports/bias_fairness_analysis.md`)

Audit of the held-out cohort (n = 885) by gender (verified encoding) and age band, at the deployed threshold and at
top-K, aggregate only; nationality, marital status, international status and special needs were profiled but not
audited as groups because most of their categories fall below the minimum reliable size.

## 2. Group metrics at the deployed threshold

| attribute | group | n | reliable | base_rate | selection_rate | tpr | fpr | brier |
|---|---|---|---|---|---|---|---|---|
| gender | female | 575 | True | 0.2452 | 0.0504 | 0.1986 | 0.0023 | 0.1081 |
| gender | male | 310 | True | 0.4613 | 0.0903 | 0.1888 | 0.0060 | 0.1364 |
| age_band | 17-19 | 403 | True | 0.1935 | 0.0199 | 0.1026 | 0.0000 | 0.0963 |
| age_band | 20-24 | 256 | True | 0.3086 | 0.0352 | 0.1139 | 0.0000 | 0.1468 |
| age_band | 25-34 | 141 | True | 0.6028 | 0.1348 | 0.2000 | 0.0357 | 0.1378 |
| age_band | 35+ | 85 | True | 0.4941 | 0.2471 | 0.5000 | 0.0000 | 0.1014 |

Attribute-level summary (reference = largest group; reliable groups only):

| attribute | reference_group | n_reliable_groups | dp_difference | di_ratio | eo_difference | eq_odds_max_diff | max_brier_gap |
|---|---|---|---|---|---|---|---|
| gender | female | 2 | 0.0399 | 0.5584 | 0.0098 | 0.0098 | 0.0283 |
| age_band | 17-19 | 4 | 0.2272 | 0.0803 | 0.3974 | 0.3974 | 0.0505 |

At top-K (50 slots) the picture is the same (`group_metrics.csv`, `operating_point = top_k`): gender DP difference
0.0372, age-band DP difference 0.2204.

## 3. Reading the numbers (author's interpretation)

**Gender.** Male students are selected at 9.0% and female students at 5.0%: a demographic-parity difference of
0.040 and a disparate-impact ratio of 0.56, below the 0.8 rule-of-thumb often quoted. But the
observed dropout base rates differ almost two-fold (46.1% vs 24.5%), and the model's **true-positive rate is nearly
identical** (0.189 vs 0.199, equal-opportunity difference 0.0098) with **false-positive rates both under 1%**.
In plain terms: among students who later dropped out, men and women had the same chance of being on the outreach list;
the list contains more men because more men dropped out in this institution's history. Whether that is acceptable depends
on the goal. If the goal is to reach students who will otherwise leave, equal opportunity is the relevant criterion and
it is met within noise. If the goal is equal outreach exposure by gender, it is not met, and the only way to meet it is
to override the model's ranking by gender (section 5), which the constitution forbids for deployment.

**Age.** This is the material finding. Selection rate rises from 2.0% (17-19) to 24.7% (35+), a DP difference of
0.227 and a DI ratio of 0.08. Base rates also rise steeply (19.4% → 60.3% → 49.4%),
so part of the gap mirrors history. But **equal opportunity is not met**: the true-positive rate is 0.103 for 17-19-year-olds
and 0.500 for students 35 and over (difference 0.397). A young student who will drop out is roughly five times less likely
to be on the outreach list than a mature student who will drop out. False-positive rates are near zero for all bands, so the
list is precise everywhere; it is recall that is unevenly distributed. Age is not a model input, so this operates through
proxies: mature entrants differ in application route (`Application mode` code 39 "Over 23 years old" is an allow-listed
feature), programme, attendance schedule, and first-semester pattern. The model has learned that those patterns carry
risk, and they do in this data, but the consequence is that younger students' dropout looks different and is under-served
by a single global threshold.

**Calibration by group** (`group_calibration.csv`, `group_calibration.png`). Brier scores range from 0.096 to
0.147 across reliable groups (max gap 0.050). Reliability curves are shown for every group with n ≥ 30.
With 85 to 575 records per group and five bins, curves for the smaller groups are indicative only.

**Subgroup sizes.** All six audited groups exceed the minimum (85 smallest, "35+"). Metric uncertainty is
still wide for that band: a TPR of 0.50 rests on 42 eventual dropouts.

## 4. Where the disparity comes from (proxy and historical-bias discussion)

- **Historical outcomes.** The label is what happened at one institution in past years. If mature students received less
  support then, their higher dropout rate is partly institutional, and a model trained to predict it will reproduce it.
- **Proxy features.** Four parental background columns (qualification and occupation of each parent) are socioeconomic
  proxies kept as model inputs by PROJECT_DECISIONS; the Milestone 4 L1 ranking placed several of their codes among the
  strongest coefficients. `Application mode` encodes an explicit over-23 route. `Course` and `Daytime/evening attendance`
  correlate with age and with working while studying. These are legitimate academic-context signals **and** channels
  through which age and class re-enter a model that excludes age itself.
- **Data scope.** One Portuguese public institution, 2008-2019 intake per the source; no Philippine or other context.
  The disparities above describe this dataset, not any other student body.

## 5. Mitigations tried (training out-of-fold; the test set was not re-used)

| variant | deployable | pr_auc | recall_at_k | precision_at_k | brier | gender_dp_difference | gender_di_ratio | gender_eo_difference | age_band_dp_difference | age_band_eo_difference |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline (deployed) | True | 0.8078 | 0.1715 | 0.9750 | 0.1286 | 0.0255 | 0.6509 | 0.0201 | 0.1107 | 0.1402 |
| reweighting (gender x label) | True | 0.8064 | 0.1724 | 0.9800 | 0.1340 | 0.0193 | 0.7203 | 0.0359 | 0.1182 | 0.1673 |
| group thresholds (equal selection by gender) | False | 0.8078 | 0.1715 | 0.9750 | 0.1286 | 0.0005 | 0.9909 | 0.0922 | 0.1089 | 0.1486 |

- **Reweighting (gender × label, Kamiran-Calders).** Refits the model; no sensitive attribute at inference, so it is
  deployable. Effect: gender DP difference 0.0193 vs 0.0255 (better), gender EO difference
  0.0359 vs 0.0201 (worse), PR-AUC 0.8064 vs 0.8078, Brier
  0.1340 vs 0.1286 (worse). Age-band gaps slightly worse. **Not adopted**: it trades a small parity gain for a
  loss in the criterion that matters most here (equal opportunity) and in calibration, and it does nothing for age.
- **Group-specific thresholds (equal selection by gender).** Closes the gender selection gap almost completely
  (0.0005) at no cost to PR-AUC, but raises the gender EO difference to 0.0922 and requires reading
  gender at decision time. **Reported, not deployed** (constitution Principle X).
- **Not tried, recommended next:** age-aware capacity allocation *by advisers* rather than by the model, i.e. reserving
  part of the outreach capacity for the younger bands where recall is lowest (section 6). This is a human-process
  mitigation that keeps the model unchanged and the sensitive attribute out of the scoring path.

No model behaviour was altered to improve these numbers; the deployed model is the Milestone 6 artifact unchanged, and
every trade-off above is recorded in `mitigation_comparison.csv`.

## 6. Residual risks and human oversight

1. **Under-reach of younger dropouts** (TPR 0.10 for 17-19). Oversight: advisers should treat the list as one input,
   keep their own referral channels for first-years, and the Equity Dashboard shows this gap explicitly.
2. **Gender composition of the list** mirrors base rates, not model error. Oversight: report list composition each cycle.
3. **Proxy channels** (parental background, application route) can re-encode age and class. Oversight: the model card lists
   them; a future iteration should test removing parental background features and report the cost.
4. **Single-institution history.** Any deployment elsewhere requires re-training, re-auditing, and local approval.
5. **Small-group uncertainty.** Metrics for the 35+ band and any nationality group are noisy; do not act on them alone.
6. **Feedback loops.** Outreach changes outcomes; retraining on post-deployment data would learn the intervention. The app
   logs actions locally and never feeds them back to the model.

## 7. What the adviser sees

Only academic and engagement factors in supportive wording (`configs/language.yaml`), never gender, age, nationality,
marital status, international status, or special needs. Sensitive attributes appear in the Equity Dashboard as
aggregate rates only.


## 6. Presentations

- **Technical deck (peers):** `notebooks/90_technical_deck.ipynb` → `reports/decks/technical_deck.slides.html`,
  12 slides: problem, dataset, leakage controls, EDA, features/selection/PCA, model comparison, final evaluation,
  explainability, fairness, reproducibility, limitations. Built from repository tables and figures.
- **Business deck (education-support leaders):** `reports/decks/business_deck_outline.md`, 10 slides with every
  figure path and number to paste, illustrative labels, and language guardrails; assembled in PowerPoint/Canva as
  `reports/decks/business_deck.pptx` (assembly checklist at the end of the outline).

## 7. Repository and reproducibility

Public repository structured as an open-source project: `src/ssn/` (data, features, modeling, explain, fairness,
reporting, app), `notebooks/` (01–05, 90), `data/` (README, dictionary; contents Git-ignored and regenerable),
`models/` (manifest committed, pipeline regenerable), `reports/`, `tests/` (165 tests), `docs/`, `configs/`,
`README.md`, `requirements.txt`, `LICENSE` (MIT; dataset CC BY 4.0). CI runs lint, secrets scan, config validation,
tests and the adviser-language scan on every push. Reproduction steps: `README.md`; full-pipeline re-run deltas:
`docs/REPRODUCIBILITY.md`.

## 8. Optional steps

- **Step 8, deployment and MLOps (attempted).** Local deployment: the Student Success Navigator Dash app
  (`python -m ssn app`; `docs/DEPLOYMENT.md`) loads the persisted pipeline without retraining and serves six pages
  with an acknowledgement-gated local action log; 30 tests cover privacy, ranking, validation, version checks, and
  the acknowledgement flow. MLOps: `docs/MLOPS.md` (pinned environment, config-driven runs, manifest versioning and
  rollback, CI on every push, monitoring plan with baselines read from the fairness and threshold files) and a
  `Dockerfile` that copies only runtime inputs (`tests/unit/test_dockerignore.py`). Demo media:
  `reports/decks/demo.gif` (8 frames — the six adviser pages, the acknowledgement modal and the
  version-mismatch page), generated in process by `scripts/render_demo_gif.py`, which asserts that no
  outcome label appears on any record-bearing frame before writing the file.
- **Step 9, Generative AI (attempted).** `docs/GENAI_USE.md` documents the use of Claude Code with Spec Kit as a
  development assistant: purposes, example prompts, human review at every milestone, data handling, and limitations.
  No generative model is part of the shipped software.

## 9. Limitations summary

See section 5.2. In one sentence: this is a well-audited prototype on one institution's historical data that ranks a
small outreach list precisely, under-reaches younger students who later leave, and must be re-trained, re-audited and
piloted locally before any use.

## 10. Rubric map

`reports/rubric_map.md` links every rubric criterion (10 + 10 + 10 + 20 + 20 + 10 + 15 + 5 = 100 points) to the files
that evidence it.
