# Deployment — Student Success Navigator (local Dash demo)

Scope: a capstone demonstration served on localhost. Not a production deployment; see the model
card and `reports/limitations.md` before any other use.

## 1. Prerequisites

- Python 3.11, git, and (first run only) internet access for the UCI download.
- A clone of the repository and an activated virtual environment:

```bash
git clone https://github.com/joopabs/student-success-navigator.git
cd student-success-navigator
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt && pip install -e .
```

## 2. Build the artifacts the app needs

The app loads a persisted pipeline and precomputed reports; it never trains. Everything below is
regenerated from the raw download by the pipeline (about 8 minutes on a laptop):

```bash
make data      # download (sha256-verified), validate, profile, clean, split -> data/demo/demo_cohort.parquet
make select && make cv && make tune
make final     # select-model, calibrate, threshold, fit-final -> models/final_pipeline.joblib + manifest.json
make explain   # reports/explainability/shap_values_test.npz (+ reference medians for phrasing)
make fairness  # reports/fairness/group_metrics.json (Equity Dashboard)
make report    # reports/model_card.md (Model Card page)
```

The app starts without `explain`, `fairness`, or `report` outputs, but shows "not available" notes on
the affected pages. It refuses to start scoring without a verified pipeline and the demo cohort.

## 3. Run

```bash
python -m ssn app                      # equivalent: python -m ssn.app
# -> Student Success Navigator at http://127.0.0.1:8050
```

Configuration (`configs/base.yaml`, section `app`): `host` (127.0.0.1), `port` (8050),
`expected_model_version` (must equal `models/manifest.json: model_version`), `actions_db`
(`data/local/actions.sqlite`). Override with `--config path/to/other.yaml`.

## 4. Pages

| Route | Page | Shows | Never shows |
|---|---|---|---|
| `/` | Overview | purpose, intended use / non-use, model version, held-out metrics, bands, illustrative capacity | — |
| `/queue` | Support Queue | de-identified cohort ranked by score; K selector (20 / 50 / 100); band; two neutral factors; retrospective aggregate note; "Record support action" | outcomes, identifiers, sensitive attributes |
| `/review/<record_id>` | Student Review | score, band, rank, neutral factors, uncertainty note, inputs used, acknowledgement button | outcomes, sensitive attributes |
| `/score` | New Record Scoring | validated form built from the manifest input schema; hypothetical result with factors | second-semester, outcome, or sensitive fields |
| `/equity` | Equity Dashboard | precomputed group metrics with n and small-group warnings, figures, mitigations, limitations | per-record data |
| `/model-card` | Model Card | `reports/model_card.md` plus monitoring, oversight and rollback guidance | — |

## 5. Acknowledgement and the local action log

Clicking "Record support action" opens a modal. **Save is disabled until the acknowledgement box is
ticked** ("I have reviewed this record myself... the decision and any action are mine"). Decisions
(record / dismiss / override) and actions (check-in message, meeting offer, share resources, no
action) are appended to `data/local/actions.sqlite` with the synthetic record id, score, band, model
version, optional reason, and a random per-process session id. The file is Git-ignored, append-only
(the module contains only CREATE TABLE and INSERT), and never read by training code.

```bash
python -m ssn actions export           # -> data/local/actions_export.csv (local review only)
sqlite3 data/local/actions.sqlite 'select count(*), min(logged_at_utc) from support_actions;'
```

If the log path is unwritable the modal reports it and scoring continues.

## 6. Version check and rollback

At startup the app verifies `manifest.model_version == app.expected_model_version` and that the
pipeline file's SHA-256 equals `manifest.pipeline_sha256`. On mismatch it serves a single blocking
page and no scores. To roll back: restore the previous `models/manifest.json` and pipeline (or
`git checkout <commit> -- models/manifest.json && make final`), set `app.expected_model_version`
to match, restart.

Test it deliberately:

```bash
sed 's/expected_model_version: "1.0.0"/expected_model_version: "9.9.9"/' configs/base.yaml > /tmp/mismatch.yaml
python -m ssn app --config /tmp/mismatch.yaml      # blocking page, no scores
```

## 7. Privacy controls (enforced by tests under `tests/app/`)

- The app reads only `models/`, `data/demo/demo_cohort.parquet`, `reports/`, and `configs/`; an AST
  test forbids imports of evaluation, tuning, and split modules and any reference to the processed
  or evaluator-only directories; another forbids any `.fit(` call.
- The demo cohort holds synthetic ids plus the 21 allow-listed features; startup refuses a cohort
  containing outcome, age-band, or sensitive columns.
- Rendering tests assert that adviser pages contain no outcome labels, identifiers, or sensitive
  column names, and that every page passes the prohibited-term scan.

## 8. Walkthrough record

| Date | Check | Result |
|---|---|---|
| 2026-09-10 | Headless start with real artifacts; six routes and `/_dash-layout` return HTTP 200 | see console log in this commit's PR / task notes |
| 2026-09-10 | Queue → open record → tick acknowledgement → Save: 3 interactions (callback-level test `test_queue_to_action_interactions.py`) | pass |
| 2026-09-10 | Version-mismatch config serves the blocking page (`test_version_check.py`) | pass |
| 2026-09-10 | `docker build -t ssn:demo .` (80 s, 372 MB image); container serves `/`, `/queue`, `/score`, `/equity`, `/model-card`, `/_dash-layout` with HTTP 200; `data/raw`, `data/processed`, `data/evaluation`, `tests/`, `notebooks/` absent inside the image | pass |
| 2026-09-11 | Demo media `reports/decks/demo.gif` (8 frames: six pages, acknowledgement modal, blocking page) generated in process by `scripts/render_demo_gif.py`; outcome-label assertion clean on every record-bearing frame | pass |

## 9. Optional container

Docker packaging is documented in Milestone 10 (`Dockerfile`, `docs/MLOPS.md`). The image must copy
only `models/`, `data/demo/`, `reports/`, and `configs/`, never the raw, processed, evaluator-only, or
local directories.
