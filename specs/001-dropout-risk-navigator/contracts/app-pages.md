# Contract: Student Success Navigator Pages

Framework: Dash Pages. Every page includes the disclaimer component and a footer with
`model_version`, `created_at`, and the illustrative-capacity label. The app never calls `fit`,
never reads `data/evaluation/` or `data/processed/`, and never displays fields marked
`adviser_visible: false` or any outcome label.

Global forbidden strings on adviser pages (tested): `Target`, `is_dropout`, outcome labels
`Dropout`/`Enrolled`/`Graduate` used as outcomes, prohibited terms from `language.yaml`.

| Route | Page | Inputs | Displays | Actions | Forbidden |
|-------|------|--------|----------|---------|-----------|
| `/` | Overview | manifest, config | Purpose, intended use, non-use, illustrative K with label, model version, cohort size, band legend, disclaimer | Navigate | Outcomes, identifiers |
| `/queue` | Support Queue | scored demo cohort, `capacity.k` | Top-K table: `record_id`, score (2 dp), band, top-2 neutral factors; notice if K > cohort; K selector limited to the K values derived from `capacity.window_sensitivity_weeks` | Open record; acknowledge review (modal) → record action / dismiss / override with optional reason | Outcomes, sensitive attributes, any name/email |
| `/review/<record_id>` | Student Review | one scored record, local SHAP, language.yaml | Score, band, ranked neutral factor phrases with direction, allow-listed feature values with labels, model version, disclaimer | Acknowledge → record action / dismiss / override | Outcomes, sensitive attributes as reasons, second-semester fields |
| `/score` | New Record Scoring | form from allow-list, `configs/ranges.json` | Validated form; result labelled "Hypothetical"; score, band, neutral factors | Submit; reset | Second-semester inputs, outcome inputs; scoring blocked on validation failure with field-level messages |
| `/equity` | Equity Dashboard | `reports/fairness/group_metrics.json` | Per attribute: table of groups with `n`, reliable flag/warning, selection rate, TPR, FPR, Brier; attribute-level DPD, DIR, EOD, equalized-odds max diff; calibration plot for reliable groups; residual-risk text from model card | Toggle attribute | Any per-record data |
| `/model-card` | Model Card | `reports/model_card.md` | Rendered markdown: intended use, non-use, data citation and licence, training data description, metrics, threshold, bands, fairness summary, limitations, version, disclaimer, test_evaluations note | None | — |

## Acknowledgement flow (queue and review)

1. Adviser clicks "Record support action".
2. Modal shows: record summary, statement "I have reviewed this record and am exercising my own
   judgement", checkbox (required), action choice (`outreach_email`, `meeting_offer`,
   `resource_share`, `no_action`), optional reason text, buttons Save / Dismiss / Override.
3. Save is disabled until the checkbox is checked. Dismiss and Override are always enabled and
   also log an entry with `acknowledged` true and the chosen `decision`.
4. On success a toast confirms "Saved locally"; on unwritable store a notice says actions cannot
   be recorded and scoring continues.

## Startup contract

1. Load config; load manifest; verify `model_version` and `pipeline_sha256`; on mismatch render
   a single blocking page with the mismatch message and exit code 0 (server stays up, no scores).
2. Load pipeline via joblib; load `data/demo/demo_cohort.parquet`; call
   `assert_frame_allowed`; `predict_proba`; assign bands and ranks.
3. Load or compute local SHAP for the cohort; map through `language.yaml`, dropping
   `adviser_visible: false` features.
4. Load `group_metrics.json` for the equity page. If absent, equity page shows "audit not yet
   run" rather than computing anything.
