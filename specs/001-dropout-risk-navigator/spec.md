# Feature Specification: Fair and Explainable Student Dropout Risk Prediction for Early Academic Support

**Feature Branch**: `001-dropout-risk-navigator`

**Created**: 2026-09-09

**Status**: Draft

**Input**: User description: "Create a complete specification for 'Fair and Explainable Student
Dropout Risk Prediction for Early Academic Support' and its Dash companion application, 'Student
Success Navigator'. Binary deployed model (is_dropout = 1 only where Target is Dropout), prediction
point at end of first semester, strict exclusion of second-semester and post-outcome features.
Decision-support for voluntary outreach only; never make or recommend adverse automated student
decisions. Cover business context, target and leakage controls, metrics, data provenance and
privacy, data quality, EDA/feature engineering/selection/PCA, baseline plus three model comparison,
evaluation design, explainability, fairness audit, report and decks, repository structure, the six
Dash pages and their safeguards, optional deployment/MLOps/GenAI documentation, risks, acceptance
criteria, and definition of done. Do not invent dataset statistics, encodings, results, business
value, or outcomes; add profiling, validation, or placeholder tasks where facts are unknown."

**Governing documents**: `CAPSTONE_BRIEF.md` (assignment and rubric), `PROJECT_DECISIONS.md`
(project decisions), `.specify/memory/constitution.md` v1.0.0 (principles and quality gates
G1-G10). This specification MUST NOT contradict any of them.

## Business Context & Scope

### Problem

Higher-education institutions lose students who leave before completing a programme. Advisers and
student-support teams have limited weekly capacity for outreach and currently lack a consistent,
explainable way to decide whom to contact first. This project builds a support-priority score,
available at the end of a student's first semester, that helps advisers prioritise voluntary,
supportive outreach to students who may benefit most from early academic support.

### Stakeholders

| Stakeholder | Interest |
|-------------|----------|
| Academic advisers and student-support staff (primary users) | A short, explainable, weekly list of students to reach out to; ability to override or dismiss suggestions |
| Students (affected parties, not users) | Receive supportive outreach; never subject to automated adverse decisions; privacy preserved |
| Student-success or equity leadership | Evidence that the tool performs consistently across student groups and that limitations are disclosed |
| Course instructor and graders | Every rubric criterion in `CAPSTONE_BRIEF.md` evidenced and traceable |
| Project author | A reproducible, professionally structured, publicly shareable capstone |

### Intended Use

- Decision support for qualified humans planning voluntary, supportive academic outreach.
- Prioritising a fixed, illustrative weekly outreach capacity (K records) among a cohort that has
  completed its first semester.
- Aggregate equity auditing of model behaviour across valid student groups.
- Educational demonstration of an end-to-end, fair, and explainable ML lifecycle.

### Explicit Non-Use

The system MUST NOT be used to make, recommend, or trigger any adverse or high-impact decision,
including denial or restriction of admission, enrollment, scholarships, financial aid, grades,
discipline, housing, or any student opportunity. Predicted scores are not causal claims and are
not statements about a student's worth or ability. The dataset originates from one institution and
MUST NOT be presented as representative of Philippine institutions or of universities generally.

### In Scope

- Binary dropout support-priority model trained on enrollment-time and first-semester features.
- Full ML lifecycle deliverables for capstone Steps 1-7.
- Student Success Navigator companion application with six pages and human-review safeguards.
- Documentation for optional Step 8 (deployment/MLOps) and Step 9 (GenAI) if attempted.

### Out of Scope

- Any integration with live institutional systems or real student records.
- Automated actions of any kind toward students.
- Retraining the model from adviser action logs.
- Multi-class prediction of Enrolled versus Graduate in the deployed workflow.
- Cloud deployment (optional, documented only if attempted).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build a Leakage-Safe, Comparable Support-Priority Model (Priority: P1)

As the project author, I need to produce a reproducible binary model that predicts first-semester
dropout support priority using only information available at the end of the first semester, and to
compare it against a trivial baseline and at least three alternative models, so that the chosen
model is defensible to graders, advisers, and equity reviewers.

**Why this priority**: Every other story depends on a trustworthy model. Steps 3, 4, and 5 of the
rubric (50 points combined) are evidenced here.

**Independent Test**: Run the documented pipeline from raw data in a fresh environment and confirm
that saved artifacts, metric tables, and comparison figures are regenerated within documented
tolerance, and that the leakage test rejects any second-semester or outcome column.

**Acceptance Scenarios**:

1. **Given** the raw dataset and the feature allow-list, **When** the training pipeline runs,
   **Then** only allow-listed enrollment-time and first-semester features reach the model, and an
   automated test fails the run if any prohibited column is present.
2. **Given** the processed training data, **When** models are trained, **Then** a trivial baseline
   plus at least three non-trivial models are tuned by cross-validation on training data only and
   evaluated once on the held-out test set.
3. **Given** the evaluation results, **When** a model is selected, **Then** the selection is
   justified in writing across primary metric, recall/precision at capacity K, calibration,
   group-level fairness, explainability, and maintainability, never on accuracy alone.
4. **Given** a fresh environment and the README, **When** a reviewer follows reproduction steps,
   **Then** reported metrics are reproduced within the documented tolerance.

---

### User Story 2 - Prioritise Weekly Voluntary Outreach from the Support Queue (Priority: P1)

As an academic adviser, I want to open the Support Queue, see the top-K de-identified records for
my illustrative weekly capacity with their risk band and neutral explanation summary, and record
that I have reviewed each and decided on a supportive action, so that outreach is consistent,
explainable, and always under my judgement.

**Why this priority**: This is the core adviser-facing value of Student Success Navigator and the
concrete demonstration of human-in-the-loop decision support.

**Independent Test**: Load the demonstration cohort, set K, confirm exactly K records appear
ranked by support-priority score, open one, acknowledge review, record a supportive action, and
confirm the action appears in the local log and never alters the model or exposes outcomes.

**Acceptance Scenarios**:

1. **Given** the demonstration cohort is loaded, **When** the adviser opens the Support Queue with
   capacity K, **Then** exactly the top K records by support-priority score are shown with synthetic
   record ID, score, risk band, and a neutral explanation summary, and no direct identifier or
   actual outcome label is visible.
2. **Given** a record in the queue, **When** the adviser attempts to record a suggested support
   action, **Then** the system requires an explicit human-review acknowledgement before the action
   is saved.
3. **Given** the adviser disagrees with a suggestion, **When** they choose to dismiss or override,
   **Then** the dismissal is recorded with an optional reason and the record is not flagged as an
   error.
4. **Given** actions have been recorded, **When** the model is retrained or the app restarted,
   **Then** the action log is unchanged in a local Git-ignored store and has not influenced any
   model input.

---

### User Story 3 - Review an Individual Record with Neutral Explanations (Priority: P2)

As an academic adviser, I want to open a single de-identified record and see which academic and
engagement factors most influenced its support-priority score, expressed in supportive, neutral
language, so that I can have an informed and respectful conversation with the student.

**Why this priority**: Explanations make the score actionable and are graded in Step 5.

**Independent Test**: Open any record from the demonstration cohort and confirm the page shows
score, band, top contributing factors in neutral wording, model version metadata, the educational
disclaimer, and no sensitive attribute presented as a reason.

**Acceptance Scenarios**:

1. **Given** a selected record, **When** the Student Review page loads, **Then** the top
   contributing factors are displayed as academic or engagement factors with supportive wording
   and no punitive terms.
2. **Given** the dataset contains sensitive attributes, **When** explanations are rendered,
   **Then** no sensitive attribute appears as an adviser-facing reason.
3. **Given** the page is rendered, **When** the adviser looks for provenance, **Then** model name,
   version, training date, and the educational disclaimer are visible.

---

### User Story 4 - Audit Equity of Model Behaviour Across Student Groups (Priority: P2)

As an equity or student-success lead, I want a written Bias & Fairness Analysis and an Equity
Dashboard that show selection rates, error rates, and calibration by valid student groups with
group sizes, so that I can judge whether the tool treats groups consistently and what residual
risks remain.

**Why this priority**: Step 5 carries 20 points and the constitution marks the fairness audit as
non-negotiable.

**Independent Test**: Open the Equity Dashboard and the report section and confirm every required
group metric is shown per valid group with sample size, that small groups carry a visible warning,
and that mitigations and residual risks are discussed.

**Acceptance Scenarios**:

1. **Given** the held-out evaluation results, **When** the Equity Dashboard loads, **Then** each
   valid group shows selection rate, demographic-parity difference, disparate-impact ratio, TPR,
   FPR, equal-opportunity difference, and calibration where sample size permits, each with n.
2. **Given** a group whose sample size is below the documented minimum, **When** metrics are
   displayed, **Then** a warning is shown and the metric is flagged as unreliable or suppressed.
3. **Given** the final report, **When** a reviewer reads the Bias & Fairness Analysis, **Then**
   mitigations attempted, their effect on fairness and performance, and residual risks are stated,
   and the report does not claim the model is fair solely because metrics fall within thresholds.

---

### User Story 5 - Score a Hypothetical New Record (Priority: P3)

As an adviser or instructor demonstrating the tool, I want to enter enrollment-time and
first-semester values for a hypothetical student and receive a support-priority score, band, and
neutral explanation, so that I can understand how the model responds to different academic
situations.

**Why this priority**: Useful for demonstration and understanding but not required for the weekly
outreach workflow.

**Independent Test**: Enter a complete valid hypothetical record and receive a score with band and
explanation; enter an invalid or incomplete record and receive a clear validation message.

**Acceptance Scenarios**:

1. **Given** the New Record Scoring form, **When** all allow-listed fields are supplied with valid
   values, **Then** a score, band, neutral explanation, and disclaimer are shown and the input is
   labelled hypothetical.
2. **Given** a field is missing or out of the documented valid range, **When** the adviser
   submits, **Then** a specific validation message identifies the field and no score is produced.
3. **Given** the form, **When** the adviser looks for second-semester inputs, **Then** none exist.

---

### User Story 6 - Consume the Report, Decks, and Model Card (Priority: P3)

As a grader, executive, or peer, I want a final report with a rubric map, a technical deck, a
business deck, and an in-app Model Card, so that I can evaluate methodology, business relevance,
risks, and limitations for my audience without reading code.

**Why this priority**: Steps 1, 2, 6, and 7 are evidenced here (45 points combined), but the
content depends on all prior stories.

**Independent Test**: Open each artifact and confirm it exists, is complete for its audience, and
maps to the rubric criteria it evidences.

**Acceptance Scenarios**:

1. **Given** the final report, **When** a grader opens the rubric map, **Then** every rubric
   criterion links to the section or artifact that evidences it.
2. **Given** the two decks, **When** counted, **Then** each has between 8 and 12 slides, one
   addressed to peers and one to executives, with all business figures labelled illustrative.
3. **Given** the Model Card page, **When** opened, **Then** intended use, non-use, data source and
   citation, metrics, fairness summary, limitations, version metadata, and disclaimer are shown.

---

### Edge Cases

- A column in the source data is neither on the allow-list nor on the documented prohibited list:
  the pipeline MUST fail with a message naming the column until it is classified.
- Capacity K exceeds the size of the demonstration cohort: the queue shows the whole cohort and
  displays a notice that capacity exceeds cohort size.
- Two or more records tie at the K boundary: the tie-break rule MUST be deterministic and
  documented.
- A group used for the fairness audit has fewer records than the documented minimum: metrics are
  suppressed or flagged unreliable and the report discusses the limitation.
- The categorical encodings in the raw data do not match the source documentation: the profiling
  task MUST surface the discrepancy and block use of the affected attribute for fairness auditing
  until resolved.
- A hypothetical record contains values outside documented valid ranges: scoring is refused with
  a field-specific message.
- The selected threshold yields zero predicted positives on the test set: the evaluation MUST
  report this and threshold selection MUST be revisited and documented.
- The saved model artifact and the app configuration report different versions: the app MUST
  refuse to serve scores and display a version-mismatch message.
- An adviser attempts to acknowledge the same record twice: the second acknowledgement is recorded
  as an additional entry, not an overwrite, so the log remains an append-only history.
- The action-log store is missing or unwritable: the app MUST inform the adviser and continue to
  display scores without recording actions.

## Requirements *(mandatory)*

### Functional Requirements

#### Business Framing and Assumptions

- **FR-001**: The final report MUST state the business problem, the data-science problem, the unit
  of analysis (one student enrollment record), the prediction point (end of first semester), the
  intended users, the intended use, and the explicit non-use.
- **FR-002**: Every business KPI, ROI, cost, or outreach-capacity figure MUST be labelled
  "illustrative" or "assumption" wherever it appears in code comments, reports, slides, and the
  application.
- **FR-003**: The business KPI MUST be expressed as the illustrative share of eventual dropout
  cases reached within a fixed voluntary-support outreach capacity K.
- **FR-004**: The final report MUST include a section-to-rubric map covering all rubric criteria in
  `CAPSTONE_BRIEF.md` Section 5.

#### Target Definition, Feature Timing, and Leakage Controls

- **FR-005**: The deployed target MUST be binary `is_dropout`, equal to 1 where the source `Target`
  equals Dropout and 0 where it equals Enrolled or Graduate. The mapping MUST be verified against
  the actual values present in the raw data before use.
- **FR-006**: The deployed model MUST use only features available at enrollment time or by the end
  of the first semester.
- **FR-007**: All second-semester features and any post-outcome information MUST be excluded from
  training, validation, test evaluation, and inference for the deployed model.
- **FR-008**: A feature allow-list and a prohibited-column list MUST be maintained in configuration
  and derived from a documented classification of every source column by availability time.
- **FR-009**: An automated test MUST fail whenever a prohibited or unclassified column reaches the
  model input.
- **FR-010**: All fitted transformations (imputation, scaling, encoding, feature selection,
  dimensionality reduction) MUST be fitted on training data or inside cross-validation folds only.
- **FR-011**: Any analysis that uses second-semester or outcome features MUST be labelled
  analysis-only and MUST be isolated from the deployed pipeline.

#### Metrics

- **FR-012**: PR-AUC for dropout versus non-dropout MUST be the primary technical metric.
- **FR-013**: Recall@K and Precision@K MUST be reported for the documented illustrative outreach
  capacity K, and for a small documented range of alternative K values for sensitivity.
- **FR-014**: Secondary metrics MUST include recall, precision, F1, ROC-AUC, confusion matrix at
  the selected threshold, precision-recall curve, and calibration curve with a calibration summary
  statistic.
- **FR-015**: All metrics MUST be reported for the trivial baseline and for every candidate model
  on the same held-out test set.

#### Data Source, Provenance, Licensing, and Privacy

- **FR-016**: The dataset MUST be the UCI Machine Learning Repository dataset "Predict Students'
  Dropout and Academic Success" (dataset 697), cited with source name, URL, authors where
  available, and access date.
- **FR-017**: The applicable UCI usage terms and dataset licence MUST be verified and recorded in
  the data documentation before the repository is made public.
- **FR-018**: The dataset MUST be described as de-identified historical data from one
  higher-education institution and MUST NOT be described as Philippine or generally
  representative.
- **FR-019**: A data dictionary MUST document every source and engineered variable with type,
  units or encoding, allowed values, availability time (enrollment, first semester, second
  semester, outcome), and source description. Encodings MUST be taken from source documentation
  and verified against the data; unverified encodings MUST be marked as such.
- **FR-020**: No personally identifiable information, direct identifiers, credentials, or secrets
  MAY be committed to version control. Action logs, environment files, and demonstration
  databases MUST be excluded from version control.
- **FR-021**: If Generative AI tools are used, raw student records MUST NOT be sent to external
  services unless the data is confirmed public and de-identified, and the usage MUST be
  documented.

#### Data Quality

- **FR-022**: The pipeline MUST profile and document missing values, duplicate records, invalid or
  out-of-range values, and outliers, with counts before and after treatment.
- **FR-023**: Treatment decisions for each data-quality issue MUST be justified in the EDA and
  Feature Engineering report and implemented in reproducible code.
- **FR-024**: Class imbalance MUST be quantified from the data and its treatment (class weighting,
  threshold selection, or resampling) MUST be justified and evaluated.
- **FR-025**: Data-quality and source limitations that cannot be resolved MUST be listed in the
  final report's limitations section.

#### EDA, Feature Engineering, Feature Selection, and PCA

- **FR-026**: Applied EDA MUST include univariate distributions, relationships with the target,
  and correlations, with figures saved under the reports directory.
- **FR-027**: Feature engineering MUST include, at minimum, first-semester approval rate,
  first-semester evaluation participation rate, first-semester non-evaluation rate, grade
  difference relative to admission grade, an age band for EDA and fairness auditing, and
  academically meaningful workload or progression measures. Each engineered feature MUST carry a
  one-line academic rationale and be constructed only from allow-listed inputs.
- **FR-028**: Denominators for rate features MUST be validated for zero or missing values and the
  handling rule documented.
- **FR-029**: At least one feature-selection technique MUST be applied and justified; the target
  is one filter method plus one embedded method where feasible.
- **FR-030**: PCA MUST be applied after encoding and scaling, fitted on training data or within
  folds only, and its effect on validated performance MUST be compared to the non-PCA pipeline.
  PCA MAY be retained for analysis and visualisation even if it does not improve the deployed
  model.

#### Model Comparison

- **FR-031**: A trivial baseline (majority or stratified dummy classifier) MUST be reported.
- **FR-032**: At least three non-trivial candidate models MUST be trained and compared:
  class-weighted logistic regression, random forest, and gradient boosting or XGBoost. A support
  vector machine MAY be added if runtime is reasonable.
- **FR-033**: Model selection MUST be justified across PR-AUC, Recall@K and Precision@K at
  capacity K, calibration, group-level fairness, explainability, and maintainability. Selection on
  accuracy alone is prohibited.

#### Evaluation Design, Tuning, Threshold, Artifacts, and Reproducibility

- **FR-034**: Data MUST be split into training and held-out test sets with stratification on the
  target, using a fixed seed. Validation MUST use cross-validation on the training set.
- **FR-035**: Hyperparameter tuning MUST use cross-validation on training data only. The held-out
  test set MUST be evaluated once for final reporting.
- **FR-036**: The decision threshold MUST be selected on training or validation data using a
  documented rule tied to outreach capacity K and error costs, and MUST be recorded with its
  rationale.
- **FR-037**: All runs MUST be driven by versioned configuration files. Random seeds MUST be
  defined once in configuration and propagated to every stochastic step.
- **FR-038**: Trained models, fitted preprocessing pipelines, feature lists, thresholds, metrics,
  and the producing configuration and code version MUST be persisted to the models and reports
  directories.
- **FR-039**: The README MUST document end-to-end reproduction from raw data to reported results
  and a running application, and a fresh environment following it MUST reproduce reported metrics
  within a documented tolerance.

#### Explainability

- **FR-040**: Global and local explanations MUST be produced for the selected model using SHAP.
  Where SHAP is infeasible for a model, permutation importance or model-native importances MUST be
  used and the substitution documented.
- **FR-041**: Partial dependence and individual conditional expectation plots MUST be produced for
  suitable continuous features; where a feature is unsuitable, the reason MUST be documented.
- **FR-042**: Explanations shown to advisers MUST be expressed as academic or engagement factors
  in supportive, neutral language. Sensitive attributes MUST NOT appear as adviser-facing reasons.
- **FR-043**: Explanation outputs MUST be saved under the reports directory and referenced in the
  final report and technical deck.

#### Fairness Audit

- **FR-044**: The final report MUST contain a "Bias & Fairness Analysis" section.
- **FR-045**: Fairness groups MUST be limited to attributes present and valid in the dataset.
  Gender (using the verified source encoding) and age band MUST be assessed. Any other attribute
  MAY be assessed only with documented ethical justification.
- **FR-046**: For each group the audit MUST report selection rate, demographic-parity difference,
  disparate-impact ratio, true-positive rate, false-positive rate, equal-opportunity difference,
  an equalized-odds discussion, and group calibration where sample size permits, each accompanied
  by the group sample size.
- **FR-047**: A documented minimum group size MUST be defined; groups below it MUST be flagged
  with a subgroup-size warning and their metrics marked unreliable or suppressed.
- **FR-048**: At least one mitigation (for example reweighting, threshold adjustment,
  augmentation, or post-processing) MUST be proposed; any implemented mitigation MUST be evaluated
  for its effect on both fairness and performance.
- **FR-049**: The audit MUST include a residual-risk discussion and MUST NOT claim the model is
  fair solely because metrics fall within a threshold.
- **FR-050**: Sensitive attributes MUST be used for aggregate auditing only and MUST NOT be
  displayed as reasons for individual scores in any adviser-facing view.

#### Final Report and Presentations

- **FR-051**: A final report MUST be produced covering Steps 1-7, the rubric map, the Bias &
  Fairness Analysis, limitations, and documentation of any optional steps attempted.
- **FR-052**: A technical presentation for peers MUST be produced with 8-12 slides recommended,
  covering methodology, visuals, and metrics.
- **FR-053**: A business-facing presentation for executives MUST be produced with 8-12 slides
  recommended, covering illustrative ROI, risks, and strategy in non-technical language.

#### Repository, Tests, and Documentation

- **FR-054**: The public repository MUST contain `src/`, `notebooks/`, `data/`, `models/`,
  `reports/`, `tests/`, `docs/`, `configs/`, `README.md`, `requirements.txt`, the final report,
  and reproducible code.
- **FR-055**: Automated tests MUST cover at minimum: target mapping, feature allow-list
  enforcement, data validation rules, engineered-feature calculations, preprocessing fit
  isolation, threshold and top-K ranking logic, action-log append behaviour, and the absence of
  identifiers and outcome labels in adviser-facing outputs.
- **FR-056**: Notebooks MUST run top-to-bottom from a clean state and MUST import shared logic
  from the source package rather than duplicating it.
- **FR-057**: Commit history MUST be clean and professional, with one logical change per commit
  and no committed secrets or large binaries.

#### Student Success Navigator Application

- **FR-058**: The application MUST provide six pages: Overview, Support Queue, Student Review, New
  Record Scoring, Equity Dashboard, and Model Card.
- **FR-059**: The Overview page MUST summarise purpose, intended use, non-use, the illustrative
  capacity K, current model version metadata, and the educational disclaimer.
- **FR-060**: The Support Queue MUST rank a de-identified held-out demonstration cohort by
  support-priority score and display exactly the top K records, with a deterministic documented
  tie-break, each showing synthetic record ID, score, risk band, and a neutral explanation
  summary.
- **FR-061**: Actual outcome labels for the demonstration cohort MUST be available to evaluation
  code only and MUST NOT be rendered on any adviser-facing page.
- **FR-062**: Risk bands MUST be defined in configuration with documented boundaries and
  supportive names; the band definition MUST be shown on the Model Card.
- **FR-063**: The Student Review page MUST show one record's score, band, top contributing
  factors in neutral language, model version metadata, and the disclaimer.
- **FR-064**: Recording a suggested support action MUST require an explicit human-review
  acknowledgement, and the adviser MUST be able to dismiss or override any suggestion with an
  optional reason.
- **FR-065**: Action records MUST be appended to a local, version-control-excluded store, MUST
  include timestamp, synthetic record ID, action, acknowledgement flag, and model version, and
  MUST NOT be used as model input.
- **FR-066**: The New Record Scoring page MUST accept only allow-listed fields, validate each
  against documented ranges, label the result hypothetical, and refuse scoring with field-specific
  messages when validation fails.
- **FR-067**: The Equity Dashboard MUST present the group-level metrics in FR-046 for the held-out
  evaluation with sample sizes and subgroup-size warnings.
- **FR-068**: The Model Card page MUST show intended use, non-use, data source and citation,
  training data description, metrics, threshold, band definitions, fairness summary, limitations,
  version metadata, and the disclaimer.
- **FR-069**: Every page MUST display the educational disclaimer stating that scores are
  illustrative decision support, not causal, and that all outreach decisions require qualified
  human review.
- **FR-070**: The application MUST refuse to serve scores when the loaded model version does not
  match the configured version and MUST display a clear message.
- **FR-071**: All adviser-facing text MUST use non-punitive language; terms such as "at risk of
  failing", "likely to drop out", or "problem student" MUST NOT appear.

#### Optional Deployment, MLOps, and Generative AI Documentation

- **FR-072**: If local deployment is attempted, a deployment guide MUST be provided in `docs/`
  and a demo recording or animated capture MUST be produced.
- **FR-073**: If MLOps practices are attempted (containerisation, experiment tracking, continuous
  checks, monitoring plan, versioning and rollback plan), each MUST be documented in the README
  or `docs/`.
- **FR-074**: If Generative AI is used, the documentation MUST state the tool, purpose, prompts or
  examples where appropriate, human review performed, and limitations, and MUST include code or
  examples in the repository or presentation.

### Key Entities *(include if feature involves data)*

- **Student Enrollment Record**: One row of the source dataset. Attributes are classified by
  availability time: enrollment-time, first-semester, second-semester, or outcome. Carries the
  source `Target` and the derived `is_dropout`.
- **Feature Allow-List / Prohibited List**: Configuration that classifies every source column and
  engineered feature as permitted for the deployed model or prohibited, with the reason.
- **Data Dictionary**: Documentation of every variable's type, encoding, allowed values,
  availability time, and verification status.
- **Model Artifact**: A trained model plus its fitted preprocessing pipeline, feature list,
  threshold, producing configuration, code version, metrics, and training date.
- **Support-Priority Score**: The model's calibrated probability-like output for one record,
  mapped to a Risk Band.
- **Risk Band**: A configured, supportively named range of scores with documented boundaries.
- **Outreach Capacity K**: The illustrative number of records an adviser can contact per period,
  defined in configuration and labelled illustrative.
- **Demonstration Cohort**: De-identified held-out records that populate the application. Their
  actual outcomes are evaluation-only.
- **Explanation**: Global feature contributions for the model and local contributions for one
  record, rendered to advisers in neutral academic or engagement language.
- **Fairness Group**: A valid grouping of records by a verified sensitive attribute, with sample
  size and the group metrics in FR-046.
- **Support Action Log Entry**: An appended record of an adviser's acknowledged review and chosen
  action, dismissal, or override, with timestamp and model version, stored locally and excluded
  from version control.
- **Model Card**: The human-readable summary of the deployed model's purpose, data, performance,
  fairness, limitations, and version.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Following the README in a fresh environment, a reviewer reproduces every reported
  metric within the documented tolerance without undocumented steps.
- **SC-002**: 100% of second-semester and outcome columns are rejected by automated validation
  before reaching the deployed model, verified by the test suite.
- **SC-003**: The selected model's PR-AUC and Recall@K on the held-out test set exceed the trivial
  baseline by a margin reported in the final report. No target value is asserted in advance; the
  actual margin is an empirical result.
- **SC-004**: A trivial baseline plus at least three non-trivial models are compared on identical
  held-out data with all metrics in FR-012 to FR-015 reported.
- **SC-005**: 100% of fairness group metrics are displayed with their group sample size, and 100%
  of groups below the documented minimum carry a warning.
- **SC-006**: An adviser can move from opening the Support Queue to recording an acknowledged
  action on one record in three or fewer page interactions.
- **SC-007**: Zero direct identifiers and zero actual outcome labels appear on any adviser-facing
  page, verified by automated test and manual review.
- **SC-008**: Zero occurrences of prohibited punitive terms appear in adviser-facing text,
  verified by automated scan.
- **SC-009**: Every rubric criterion in `CAPSTONE_BRIEF.md` Section 5 maps to at least one
  evidencing artifact in the final report's rubric map.
- **SC-010**: Both slide decks contain between 8 and 12 slides.
- **SC-011**: Every business or capacity figure in reports, slides, and the application carries
  an "illustrative" or "assumption" label, verified by review.
- **SC-012**: The public repository passes a secrets scan and contains all directories and files
  listed in FR-054.

## Assumptions

- The UCI dataset is publicly downloadable and its terms permit educational use; this MUST still
  be verified and recorded before publication (FR-017).
- The source `Target` contains exactly the three values Dropout, Enrolled, and Graduate; the actual
  values MUST be verified before the binary mapping is finalised.
- Column names in the source data allow first- and second-semester features to be distinguished
  reliably; the classification of every column MUST be documented and reviewed.
- The held-out test split serves as the de-identified demonstration cohort for the application.
  It is evaluated once for reporting and its outcome labels are never shown to advisers.
- Outreach capacity K is a configurable illustrative value with a documented default chosen during
  planning; the spec does not assert any real institutional capacity.
- Age bands are defined during planning after profiling the age distribution, with boundaries
  documented and justified; the spec does not assert specific boundaries.
- Risk band boundaries are defined during planning relative to the selected threshold and
  capacity K, with supportive names; the spec does not assert specific boundaries.
- The minimum group size for fairness reporting is defined during planning and documented; the
  spec does not assert a specific value.
- A single local user operates the application; authentication and multi-user roles are out of
  scope for this capstone.
- Reproduction tolerance for metrics is defined during planning, with any residual nondeterminism
  from libraries documented.
- Cloud deployment, live data integration, and model retraining from action logs are out of scope.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Temporal leakage through mislabelled columns or engineered features | Inflated metrics; useless at decision point | Column classification review, allow-list in configuration, automated leakage test (FR-008, FR-009) |
| Misread categorical encodings (including gender) | Wrong features and invalid fairness audit | Verify encodings against source documentation and data before use; mark unverified encodings (FR-019, FR-045) |
| Historic institutional inequities encoded in outcomes | Model reproduces bias | Fairness audit, mitigations, residual-risk discussion, aggregate-only use of sensitive attributes (FR-044 to FR-050) |
| Small subgroups produce unstable fairness metrics | Misleading conclusions | Minimum group size with warnings and suppression (FR-047) |
| Class imbalance misleads accuracy-based comparison | Poor model choice | PR-AUC primary, Recall@K, prohibition on accuracy-only selection (FR-012, FR-033) |
| Misuse of scores for adverse decisions | Harm to students; violation of constitution | Explicit non-use, disclaimer on every page, human acknowledgement, no automated actions (FR-064, FR-069) |
| Overclaiming generalisation or business value | Misleading stakeholders; rubric penalty | Illustrative labels, single-institution statement, limitations section (FR-002, FR-018, FR-025) |
| Irreproducible results | Loss of Step 4 and Step 7 credit | Fixed seeds, configs, saved artifacts, reproduction test (FR-037 to FR-039) |
| Accidental commit of data, logs, or secrets | Privacy breach; unrecoverable | Version-control exclusions, secrets scan, review before public push (FR-020, SC-012) |
| Dependency or runtime constraints on heavier models | Incomplete comparison | Optional SVM only if runtime reasonable; document any model omitted (FR-032) |

## Unknown Empirical Facts: Profiling, Validation, and Placeholder Tasks

The following facts are intentionally not asserted in this specification. Each MUST be established
by a profiling or validation task before dependent work proceeds, and the result recorded in the
data documentation or final report.

- **PV-01**: Record count, column count, and the exact set of column names in the raw dataset.
- **PV-02**: Actual values and frequencies of `Target`; confirm the three expected classes and the
  resulting `is_dropout` class balance.
- **PV-03**: Classification of every column by availability time (enrollment, first semester,
  second semester, outcome), reviewed and recorded as the allow-list and prohibited list.
- **PV-04**: Encoding of every categorical variable, taken from UCI documentation and verified
  against observed values, including the gender encoding used for fairness grouping.
- **PV-05**: Missing-value counts, duplicate counts, invalid or out-of-range values, and outlier
  candidates per column.
- **PV-06**: Age distribution and the resulting age-band boundaries with justification.
- **PV-07**: Group sample sizes for gender and age bands, and the resulting minimum group size
  policy.
- **PV-08**: Presence of zero or missing denominators for engineered rate features.
- **PV-09**: Applicable UCI licence and usage terms, with citation text and access date.
- **PV-10**: Default illustrative outreach capacity K and the sensitivity range of K values.
- **PV-11**: Baseline and candidate model results, calibration, and threshold; all values are
  empirical outputs of the pipeline.
- **PV-12**: Fairness metric values and their interpretation; all values are empirical outputs of
  the audit.
- **PV-13**: Reproduction tolerance observed across two independent fresh-environment runs.

## Definition of Done

This feature is done when all of the following hold:

- Constitution quality gates G1 through G10 pass with linked evidence.
- All functional requirements FR-001 to FR-071 are satisfied; FR-072 to FR-074 are satisfied for
  any optional step attempted, or the step is recorded as not attempted.
- All success criteria SC-001 to SC-012 are verified.
- All profiling and validation tasks PV-01 to PV-13 have recorded results.
- Every required deliverable in `CAPSTONE_BRIEF.md` Section 8 exists and is traceable from the
  README and the rubric map.
- The repository is public, passes a secrets scan, contains no private data or course material,
  and has a clean commit history.
- Submission files are renamed per course instructions and uploaded.
