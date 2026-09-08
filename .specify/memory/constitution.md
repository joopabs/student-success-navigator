<!--
Sync Impact Report
==================
Version change: (template, unversioned) -> 1.0.0
Bump rationale: Initial ratification. All template placeholders replaced with
project-specific governance for the Student Success Navigator capstone.

Modified principles: N/A (initial ratification; template placeholders replaced)

Added sections:
- Core Principles I-XII (template provided 5 placeholder slots; expanded to 12
  because the user input enumerates 12 distinct enforceable areas)
- Additional Constraints & Prohibited Uses (fills [SECTION_2_NAME])
- Quality Gates & Definition of Done (fills [SECTION_3_NAME])
- Governance (rules filled)

Removed sections: none

Templates requiring review (not modified by this command):
- .specify/templates/plan-template.md: Constitution Check gate should
  reference Quality Gates G1-G10 below.
- .specify/templates/spec-template.md: no structural change required.
- .specify/templates/tasks-template.md: no structural change required.

Follow-up TODOs: none. No placeholders deferred.
-->

# Student Success Navigator Constitution

Project: Fair and Explainable Student Dropout Risk Prediction for Early Academic
Support (Pillar 5 Capstone, Education domain). Companion application: Student
Success Navigator, a Dash web application.

Authoritative inputs: `CAPSTONE_BRIEF.md` (assignment requirements and rubric)
and `PROJECT_DECISIONS.md` (project-specific decisions). Where this constitution
and those documents conflict, this constitution governs and the conflict MUST be
resolved by amendment.

## Core Principles

### I. Assignment Fidelity & Rubric Traceability

- Every deliverable named in `CAPSTONE_BRIEF.md` Steps 1-7 MUST exist in the
  repository and be traceable from the README to its location.
- Work MUST target the "Outstanding/Exemplary" band of every rubric criterion.
  The 100-point allocation is fixed: Steps 1, 2, 3, and 6 at 10 points each;
  Steps 4 and 5 at 20 points each; Step 7 at 15 points; bonus at 5 points,
  included inside the 100 total.
- Optional Steps 8 (Deployment & MLOps) and 9 (Generative AI) MAY be pursued.
  If pursued, they MUST be documented to the same standard as required steps
  because they tie into the 5 bonus points together with creative presentation.
- The final report MUST contain a section-to-rubric mapping so a grader can
  locate evidence for each criterion without searching.

Rationale: the rubric is the acceptance test for this project. Untraceable work
earns no credit regardless of quality.

### II. Business Framing, Task Definition & Labeled Assumptions

- The problem statement MUST state the business problem, the data-science
  problem, the unit of analysis (one student enrollment record), the prediction
  point (end of first semester), and the intended user (academic advisers and
  student-support teams).
- The task MUST be declared as binary classification with target `is_dropout`
  (Dropout = 1; Enrolled or Graduate = 0), derived from the source `Target`.
- The primary technical metric MUST be PR-AUC. Recall at top K, where K is a
  documented illustrative weekly outreach capacity, MUST be reported as the
  intervention-sensitive metric. Secondary metrics listed in
  `PROJECT_DECISIONS.md` MUST be reported.
- Every business KPI, ROI figure, cost figure, or outreach-capacity value MUST
  be explicitly labeled "illustrative" or "assumption" at each place it appears
  in code comments, reports, and slides. Unlabeled business numbers are a defect.
- Predicted risk MUST be described as a support-priority score, never as a
  causal claim or a prediction about an individual's worth or ability.

Rationale: Step 1 is graded on measurable, well-explained metrics and KPIs. The
dataset carries no institutional cost data, so honesty requires labeling.

### III. Data Provenance, Licensing & Privacy (NON-NEGOTIABLE)

- The dataset MUST be cited with source name, URL, authors where available, and
  access date: UCI Machine Learning Repository, "Predict Students' Dropout and
  Academic Success", https://archive.ics.uci.edu/dataset/697/.
- Applicable UCI usage terms and the dataset license MUST be verified and
  recorded in `data/README.md` before any public publication of the repository.
- The dataset MUST be described as de-identified historical data from one
  higher-education institution. It MUST NOT be represented as data from a
  Philippine university or as representative of all universities.
- No personally identifiable information, direct student identifiers,
  credentials, API keys, tokens, or secrets MAY be committed to Git. Local
  action logs, `.env` files, and demonstration databases MUST be Git-ignored.
- Any GenAI tool usage MUST NOT transmit raw student records outside the local
  environment unless the data is confirmed public and de-identified.

Rationale: Step 2 requires source citation; privacy failures cannot be undone
once pushed to a public repository.

### IV. Reproducibility by Default

- All random operations MUST use a fixed seed defined once in configuration and
  propagated to data splits, cross-validation, model initialization, and any
  sampling.
- Every training, evaluation, and app run MUST be driven by a versioned
  configuration file (for example `configs/*.yaml`). Hard-coded hyperparameters
  in scripts or notebooks are a defect.
- Trained model artifacts, fitted preprocessing pipelines, feature lists, and
  evaluation metrics MUST be saved to `models/` and `reports/` with the
  producing configuration and code version recorded alongside them.
- `requirements.txt` MUST pin versions sufficient to recreate results. A fresh
  environment following the README MUST reproduce reported metrics within
  documented tolerance.
- Automated tests MUST exist for data validation, feature availability rules,
  preprocessing, and application logic, and MUST pass before any merge to main.
- The README MUST document end-to-end reproduction steps from raw data to
  reported results and running app.

Rationale: Step 4 and Step 7 both grade reproducibility; it is also the only
defense against silent leakage and drift in results.

### V. Leakage-Safe Temporal Feature Availability (NON-NEGOTIABLE)

- The deployed model MUST use only features available at enrollment time or by
  the end of the first semester.
- All second-semester features (curricular units enrolled, evaluations,
  approvals, grades, without evaluations) and any post-outcome information MUST
  be excluded from training, validation, and inference for the deployed model.
- An explicit allow-list of permitted features MUST live in configuration, and
  an automated test MUST fail if any prohibited column reaches the model.
- Any exploratory analysis that touches second-semester features MUST be
  clearly labeled as analysis-only and MUST NOT feed the deployed pipeline.
- All fitted transformations (imputers, scalers, encoders, feature selectors,
  PCA) MUST be fit on training data or inside cross-validation folds only.

Rationale: a model that peeks at second-semester or outcome data is useless at
the actual decision point and inflates every reported metric.

### VI. Documented Data Quality Treatment

- The EDA and Feature Engineering report MUST document, with reproducible code,
  the detection and treatment of missing values, duplicates, invalid or
  out-of-range values, and outliers, including counts before and after.
- Class imbalance MUST be quantified and its treatment (class weights,
  threshold selection, or resampling) MUST be justified and evaluated.
- A data dictionary MUST cover every variable with type, units or encoding,
  allowed values, and source description. Encodings of categorical codes MUST
  be verified against the UCI documentation before use.
- Data-quality limitations that could not be resolved MUST be listed in the
  final report's limitations section.

Rationale: Steps 2, 3, and 5 each grade this explicitly, and unverified code
encodings would corrupt both features and fairness audits.

### VII. Evidence-Based EDA, Feature Engineering & Selection

- Applied EDA MUST include distributions, relationships with the target, and
  correlations, with visuals saved to `reports/figures/`.
- Feature engineering MUST be domain-informed and MUST include, at minimum,
  first-semester approval rate, evaluation participation rate, non-evaluation
  rate, grade difference relative to admission grade, and an age band used for
  EDA and fairness auditing. Each engineered feature MUST carry a one-line
  academic rationale.
- At least one feature-selection technique MUST be applied and justified. The
  target is one filter method plus one embedded method where feasible.
- PCA MUST be applied after encoding and scaling, fitted on training data or
  within folds only, and its effect on validated performance MUST be compared.
  PCA MAY be retained for analysis and visualization even if it does not
  improve the deployed model.

Rationale: Step 3 requires at least one selection method plus dimensionality
reduction, used and justified.

### VIII. Baseline-Anchored Multi-Criteria Model Selection

- A `DummyClassifier` baseline MUST be reported alongside every candidate.
- At least three appropriate non-trivial models MUST be trained and compared.
  Candidates are class-weighted Logistic Regression, Random Forest, Gradient
  Boosting or XGBoost, and optionally SVM if runtime is reasonable.
- Hyperparameters MUST be tuned with cross-validation on training data only.
  The held-out test set MUST be evaluated once for final reporting.
- Model selection MUST be justified across PR-AUC, recall/precision trade-offs
  at the documented outreach capacity K, calibration, group-level fairness,
  explainability, and maintainability. Selection by accuracy alone is
  prohibited.
- The chosen decision threshold MUST be documented with its rationale relative
  to outreach capacity and error costs.

Rationale: Step 4 carries 20 points and grades multi-model comparison and clear
reasoning for choice; accuracy is misleading under imbalance.

### IX. Explainability as a Deliverable

- Global and local explanations MUST be produced for the selected model using
  SHAP. If SHAP is infeasible for a model, permutation importance or
  model-native importances MUST be used and the substitution documented.
- PDP and ICE plots MUST be produced for suitable continuous features. LIME MAY
  be used as a supplementary local method.
- Explanations shown to advisers in the app MUST be expressed as academic and
  engagement factors in supportive language. Sensitive attributes MUST NOT
  appear as adviser-facing reasons.
- Explanation outputs MUST be saved to `reports/` and referenced in the final
  report and technical deck.

Rationale: Step 5 grades explainability tools explicitly, and advisers cannot
act responsibly on unexplained scores.

### X. Ethical AI & Fairness Audit (NON-NEGOTIABLE)

- A "Bias & Fairness Analysis" section MUST appear in the final report.
- Sensitive attributes MUST be limited to those present and valid in the
  dataset. Gender and age band MUST be assessed. Other fields MAY be assessed
  only with documented ethical justification.
- Group metrics MUST include selection-rate comparison, demographic parity
  difference, disparate-impact ratio, TPR and FPR comparison, equal-opportunity
  difference, equalized-odds discussion, and group calibration where sample
  sizes permit. Group sample sizes MUST be reported next to every group metric.
- Sensitive attributes MUST be used for aggregate auditing only. They MUST NOT
  be presented as adviser-facing decision reasons in the app or reports.
- Concrete, feasible mitigations MUST be proposed and, where implemented,
  evaluated for their effect on both fairness and performance.
- The report MUST NOT claim the model is "fair" solely because metrics fall
  within a threshold. Limitations of the audit MUST be stated.
- Data and model limitations (imbalance, leakage risk, overfitting, single
  institutional context, historic inequities, non-causal predictions) MUST be
  discussed in the final report.

Rationale: Step 5 carries 20 points, and an unaudited dropout model can
entrench the inequities it was built to reduce.

### XI. Human-in-the-Loop Decision Support Only (NON-NEGOTIABLE)

- Student Success Navigator is a support-prioritization tool for qualified
  humans. It MUST NOT make, recommend, or trigger any adverse decision.
- The following automated decisions are prohibited in any code path, document,
  or demonstration: denial or restriction of admission, enrollment,
  scholarships, financial aid, grades, discipline, housing, or any student
  opportunity.
- All adviser-facing text MUST use non-punitive, supportive language. Terms
  such as "at risk of failing", "likely to drop out", or "problem student" MUST
  NOT appear in the UI; use "support priority" or equivalent.
- The app MUST NOT display direct identifiers. Demonstration records MUST be
  keyed by synthetic record IDs.
- Actual outcomes are evaluation-only and MUST NEVER appear on adviser-facing
  pages.
- Recording any suggested support action MUST require an explicit human-review
  acknowledgement step, and advisers MUST be able to override or dismiss any
  suggestion. Action logs MUST be stored locally, Git-ignored, and MUST NOT be
  fed back into the current model.
- The app MUST present a model card stating intended use, non-use, limitations,
  and the fairness audit summary.

Rationale: the intended use is voluntary, supportive outreach. Anything else is
a misuse of the model and out of scope for this project.

### XII. Communication & Repository Professionalism

- Two slide decks MUST be produced, each recommended at 8-12 slides: a
  technical deck for peers (methodology, visuals, metrics) and a business deck
  for executives (ROI labeled illustrative, risks, strategy) in non-technical
  language.
- The public GitHub repository MUST be structured like an open-source project
  with `src/`, `notebooks/`, `data/`, `models/`, `reports/`, `tests/`,
  `README.md`, `requirements.txt`, the final report, and reproducible code.
- Commit history MUST be clean and professional: imperative messages, one
  logical change per commit, no committed secrets or large binaries.
- Optional work MUST be documented where it exists: Dash deployment in
  `docs/DEPLOYMENT.md`; MLOps practices, Docker, and CI in the README or
  `docs/`; GenAI use with tool, purpose, prompts or examples, human review, and
  limitations. Optional work that is undocumented does not count as done.

Rationale: Steps 6 and 7 together carry 25 points and are graded on
presentation quality and repository structure.

## Additional Constraints & Prohibited Uses

- **Technology stack**: Python 3, scikit-learn as the primary modelling
  library, XGBoost or scikit-learn Gradient Boosting permitted, SHAP for
  explainability, Dash for the companion app, pytest for tests. Additions MUST
  be justified in the plan and pinned in `requirements.txt`.
- **Data location**: Raw data MUST live under `data/raw/` and MUST NOT be
  modified in place. Processed data MUST be regenerable from raw data by code.
  Large or licensed files MAY be Git-ignored with download instructions in
  `data/README.md`.
- **Secrets**: No credentials in code, configs, notebooks, or Git history.
  Environment variables via a Git-ignored `.env` only.
- **Notebooks**: Notebooks MUST be executable top-to-bottom from a clean kernel
  and MUST import reusable logic from `src/` rather than duplicating it.
- **Course material**: `references/Pillar5_Capstone_Project.pdf` is private
  course material, MUST remain Git-ignored, and MUST NOT be modified.
- **Prohibited representations**: The project MUST NOT claim generalization to
  Philippine or other institutions, causal effects, or fairness guarantees.
- **Prohibited uses**: See Principle XI. These prohibitions apply to code,
  documentation, slides, demos, and any GenAI-generated content.

## Quality Gates & Definition of Done

Each gate MUST pass before the corresponding phase is considered complete. Gate
evidence MUST be linked from the final report's rubric map.

| Gate | Phase | Pass criteria |
|------|-------|---------------|
| G1 | Framing | Problem statement, task type, unit of analysis, prediction point, primary and secondary metrics, and labeled business assumptions are written and reviewed. |
| G2 | Data | Source cited, license/terms recorded, data dictionary complete, encodings verified, dataset overview with missingness, outliers, and distributions produced. |
| G3 | Leakage | Feature allow-list in config; automated test rejects second-semester and outcome columns; all transformers fit inside training data or folds. |
| G4 | Preprocessing & EDA | Missingness, duplicates, invalid values, outliers, and imbalance treated and documented with before/after counts; EDA figures saved; at least one feature-selection method and PCA applied and justified. |
| G5 | Modelling | Dummy baseline plus at least three models tuned via CV; single final test evaluation; PR-AUC, Recall@K, Precision@K, calibration, and confusion matrix reported; selection justified across all Principle VIII criteria. |
| G6 | Explainability | SHAP global and local outputs (or documented fallback), PDP/ICE for suitable features, saved to `reports/`. |
| G7 | Fairness | Bias & Fairness Analysis written with group sizes, required metrics, mitigations, and audit limitations; no sensitive attribute used as adviser-facing reason. |
| G8 | Application | Dash app runs locally from README steps; model card, support queue with capacity K, record review, hypothetical scoring, fairness dashboard, and acknowledgement flow present; no identifiers or actual outcomes on adviser pages; non-punitive language verified. |
| G9 | Reproducibility | Fresh environment reproduces reported metrics within documented tolerance; all tests pass; artifacts and configs saved; seeds fixed. |
| G10 | Communication & Repo | Two decks at 8-12 slides each; final report with rubric map; repository structure complete; commit history clean; optional work documented. |

**Definition of Done for the capstone**: all gates G1-G10 pass; every required
deliverable in `CAPSTONE_BRIEF.md` Section 8 is present; no open item in the
submission checklist; the repository is public with no secrets or private data;
and the submission files are renamed per course instructions.

**Definition of Done for any feature or pull request**: the change is covered by
tests that pass; it does not violate any NON-NEGOTIABLE principle; configs and
artifacts it produces are saved; documentation it affects is updated; and the
commit message describes one logical change.

## Governance

- This constitution supersedes all other practices, templates, and ad hoc
  decisions in this repository. `PROJECT_DECISIONS.md` records decisions; where
  it conflicts with this document, this document governs until amended.
- **Amendment procedure**: propose the change in a commit that edits this file,
  update the Sync Impact Report comment, bump the version, set Last Amended to
  the commit date, and record the rationale in the commit message. Amendments
  that weaken a NON-NEGOTIABLE principle MUST include a written justification in
  the final report's limitations section.
- **Versioning policy**: semantic versioning. MAJOR for removing or redefining a
  principle in a backward-incompatible way; MINOR for adding a principle or
  section or materially expanding guidance; PATCH for clarifications and wording.
- **Compliance review**: every plan MUST include a Constitution Check that maps
  the feature to affected principles and gates. Every pull request MUST state
  which gates it advances and confirm no NON-NEGOTIABLE principle is violated.
  Complexity beyond the stated stack MUST be justified in the plan.
- **Runtime guidance**: `CAPSTONE_BRIEF.md` for assignment requirements and
  `PROJECT_DECISIONS.md` for project decisions. Agents and contributors MUST
  read both before planning work.

**Version**: 1.0.0 | **Ratified**: 2026-09-09 | **Last Amended**: 2026-09-09
