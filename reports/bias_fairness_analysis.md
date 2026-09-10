# Bias & Fairness Analysis

**Generated:** 2026-09-10 from `reports/fairness/group_metrics.{csv,json}`, `attribute_summary.csv`, `group_calibration.csv`,
`mitigation_comparison.csv`, `reports/tables/ablation_sensitive.csv`, `eda_dropout_rate_by_sensitive_group.csv`, and
`models/manifest.json`. Figures: `reports/fairness/selection_rates.png`, `group_calibration.png`. Numbers are copied
from those files; interpretation is the author's and is marked as such.

> This analysis reports observed disparities. It does not, and cannot, establish fairness. Fairness is a
> property of the whole decision process (data, model, threshold, adviser practice, institutional response), and the
> data come from one institution's past outcomes.

## 1. What was audited and why

- **Cohort:** the held-out test split, n = 885, scored once by the persisted final model (calibrated random
  forest, version 1.0.0). Labels come from the evaluator-only file; the app never sees them.
- **Attributes:** gender and age band, the two attributes PROJECT_DECISIONS designates for auditing. **Gender encoding**
  {'1': 'male', '0': 'female'} was verified against the UCI variables table (`data/data_dictionary.md`); the audit code refuses
  to run if that flag is false. **Age bands** (17-19, 20-24, 25-34, 35+) were set from the training age distribution
  in Milestone 3 (PV-06). Nationality, marital status, international status, and special needs were profiled in the
  EDA but are **not audited as groups** here: in the training split 19 of the nationality groups and three of the marital-status
  groups fall below the minimum reliable size (30), so group metrics would be noise. They remain
  candidates for a future audit with pooled categories and documented justification.
- **Operating points:** the deployed capacity threshold (0.9728) and the top-K list (K = 50), because
  advisers use the ranked list, not the threshold alone.
- **Guarantees already in place:** none of the six sensitive attributes is a model input (`configs/features.yaml`,
  enforced by `tests/unit/test_features_yaml_complete.py`), and none can appear as an adviser-facing reason
  (`configs/language.yaml` `adviser_visible: false`, enforced by `tests/unit/test_language_no_sensitive_reasons.py`).
  Excluding them cost at most 0.0065 PR-AUC in cross-validation (`ablation_sensitive.csv`).

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
