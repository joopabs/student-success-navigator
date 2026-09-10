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
