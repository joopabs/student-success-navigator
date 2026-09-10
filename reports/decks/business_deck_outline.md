# Business Deck Outline — Student Success Navigator

**Audience:** education-support leaders and executives. **Format:** PowerPoint or Canva, **10 slides** (8–12 recommended).
**Generated:** 2026-09-10 from repository outputs; every number below cites its source file. Figures to paste are listed per
slide with their repository path. All capacity, window, and "share reached" figures are **ILLUSTRATIVE** assumptions and
must carry that label on the slide. No cost, saving, or return figure exists in the data and none should be added.

**Language guardrails for every slide:** the tool *suggests* a short outreach list; it does not predict any student's future
with certainty, does not replace advisers, is not shown to cause better outcomes, and can make no adverse decision.

---

## Slide 1 · Title
- "Student Success Navigator: earlier, fairer, supportive outreach after the first semester"
- Subtitle: a decision-support prototype built on one institution's public data (UCI, CC BY 4.0) — illustrative, not deployed
- Footer: model version 1.0.0 · reports/model_card.md

## Slide 2 · The student-support opportunity
- Message: many students who leave show academic warning signs in their first semester; advisers have limited time to reach them.
- Data point (measured, this dataset): 1421 of 4,424 students in the historical dataset did not complete (32%) — `reports/tables/profile_target.csv`
- Opportunity statement: prioritise *voluntary, supportive* conversations with the students most likely to benefit, within advisers' existing time.
- Avoid: any claim that outreach reduces dropout; that is the hypothesis a pilot would test.

## Slide 3 · How advisers would use it (workflow)
- Diagram: end of semester 1 → support-priority score → **Support Queue** (top-K list, supportive bands) → adviser reviews each record → conversation / referral / dismiss → decision recorded locally → nothing feeds back to the model.
- Three visible safeguards: human acknowledgement before any action, no student identifiers or outcome labels shown, neutral academic language only.
- Source: `specs/001-dropout-risk-navigator/contracts/app-pages.md`; screenshots from Milestone 9 when available.

## Slide 4 · What the score is made of (and what it is not)
- Inputs: enrollment details and first-semester results only (21 columns + 7 derived indicators such as share of first-semester units passed).
- Top drivers (measured, SHAP): sem1_approval_rate, Curricular units 1st sem (approved), Curricular units 1st sem (grade), grade_diff_vs_admission — `reports/explainability/shap_global_importance.csv`; figure `reports/explainability/shap_global_bar.png`
- **Not inputs:** anything from the second semester, financial-status flags with unclear timing, and gender, age, nationality, marital status, international status, special needs.
- One-liner: "the score reflects how the first semester went, not who the student is".

## Slide 5 · Measured performance (held-out test, evaluated once)
| | Final model | Chance baseline |
|---|---|---|
| Ranking quality (PR-AUC) | **0.82** | 0.32 |
| Of the top-50 list, later dropped out (Precision@K) | **96%** | 42% |
| Calibration error (lower is better) | 0.034 | — |
- Source: `reports/tables/test_metrics_all_models.csv`; figure `reports/figures/test_pr_curve.png`
- Plain reading: "when the model puts a student on a 50-person list, about 96 in 100 later dropped out; for a random list it would be about 42 in 100."
- Say explicitly: measured on one institution's historical data; a local pilot must re-measure.

## Slide 6 · Illustrative outreach-capacity impact (label the slide ILLUSTRATIVE)
- Assumption: **10 conversations per adviser-week over a 5-week window = 50 students per cohort of 885** (illustrative).
| Outreach window (illustrative) | Students contacted | Share of eventual dropouts reached (measured recall) | Contacted who did drop out (measured precision) |
|---|---|---|---|
| 2 weeks | 20 | 7% | 95% |
| 5 weeks | 50 | 17% | 96% |
| 10 weeks | 100 | 33% | 93% |
- Source: `reports/tables/test_recall_precision_at_k.csv` (284 eventual dropouts in the 885-student test cohort).
- Key sentence: "reach is limited by adviser capacity, not by the model — more weeks, more students reached; the list stays precise."
- Do not convert to money. No cost or saving data exists in this project.

## Slide 7 · Ethical safeguards built in
- Leakage-safe: only information available at the prediction point (tested).
- Sensitive attributes are never inputs and never shown as reasons; used only to audit outcomes by group (tested).
- Human-in-the-loop: acknowledgement before any recorded action; advisers can dismiss or override; actions stay local; no feedback into the model.
- Non-use policy (constitution): no automated or adverse decision on admission, enrollment, aid, grades, discipline, housing.
- Source: `.specify/memory/constitution.md`, `reports/model_card.md`.

## Slide 8 · What the fairness audit found (be direct)
| Group comparison (held-out cohort) | Selection gap | Among students who did drop out, chance of being on the list |
|---|---|---|
| Women vs men | 5.0% vs 9.0% | 20% vs 19% (near equal) |
| Age 17–19 vs 35+ | 2.0% vs 24.7% | **10% vs 50%** |
- Source: `reports/fairness/group_metrics.csv`; figure `reports/fairness/selection_rates.png`
- Message: the list reflects historical patterns; younger students who leave are under-reached. Recommended response is an adviser-side rule (reserve part of the outreach list for first-years), not a change to the model. Full discussion: `reports/bias_fairness_analysis.md`.

## Slide 9 · Risks and governance
- Risks: historical bias in outcomes; proxy features (parental background, application route); single-institution scope; small subgroups; feedback loops if retrained on outreach data.
- Governance in place: written constitution, model card, fairness audit, limitations, reproducible pipeline (fresh-environment re-run: zero deltas), CI on every change, version-checked artifact, local action log.
- What a pilot would need: institutional approval, local data agreement, re-training and re-audit, adviser training, a review cadence for the Equity Dashboard.

## Slide 10 · Next steps and the ask
- Decide whether to pilot with local data under the governance above.
- Resolve the open data question (timing of financial-status fields) with the data owner before any local build.
- Pilot design: measure whether outreach changes outcomes (the model does not show this); track list composition by group each cycle.
- Ask: sponsorship for a time-boxed pilot with an equity review checkpoint, not a deployment decision.

---

### Assembly checklist (fill in when the deck is built — T073)
- [ ] Slide count between 8 and 12: ______  (this outline = 10)
- [ ] Every capacity / window / share-reached figure labelled "illustrative"
- [ ] No cost, saving, or return figure added
- [ ] No claim of certainty, causation, adviser replacement, or adverse decision
- [ ] Figures pasted from the paths above (no re-drawn numbers)
- [ ] Exported file saved as `reports/decks/business_deck.pptx`; date and final slide count recorded here: ______
