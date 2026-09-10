# MLOps Notes — Student Success Navigator

**Scope:** a capstone prototype. These notes describe how the project is kept reproducible, versioned, checked, and
how it would be monitored and rolled back if it were ever piloted. They are not a claim of production readiness.
Written 2026-09-10; baselines below are read from the files named in each section.

## 1. Reproducible environment

- Python 3.11 (`.python-version`); dependencies pinned to the exact versions that produced the artifacts in
  `requirements.txt` / `requirements-dev.txt`; the package installs with `pip install -e .`.
- Recorded in `models/manifest.json`: Python 3.11.12; scikit-learn 1.9.0, numpy 2.4.6, pandas 3.0.5, shap 0.51.0, imbalanced-learn 0.14.2, joblib 1.6.0, ssn 0.1.0.
- A second run in a fresh virtual environment reproduced every compared table with a maximum absolute delta of 0
  (`docs/REPRODUCIBILITY.md`, `python -m ssn reproduce-check`). Final fit uses `n_jobs=1`; CV and search are seeded.
- Optional container: `Dockerfile` + `.dockerignore` (section 5) package the app with its artifacts only.

## 2. Config-driven runs

Every command reads `configs/base.yaml` (one seed, paths, illustrative capacity, thresholds, fairness settings) and
`configs/models/*.yaml`; no hyperparameter or path is hard-coded. The `Makefile` targets chain the CLI in the
documented order (`make data … make report`). `python -m ssn config validate` fails fast on a malformed config
(e.g. an `illustrative` flag set to false, or K not equal to per-week × window).

## 3. Versioning and rollback

- **Identity of a model:** `models/manifest.json` (committed) records `model_version`, git SHA, config hash,
  pipeline SHA-256, library versions, seed, input schema, threshold, bands, and the held-out evaluation counter.
  The pipeline file itself (`models/final_pipeline.joblib`, e969a32296f6…) is Git-ignored and regenerated with
  `make final`; its checksum must match the manifest or the app refuses to serve.
- **Bumping:** change `project.model_version` and `app.expected_model_version` together in `configs/base.yaml`,
  re-run `make final` (which re-evaluates the held-out set exactly once and increments `test_evaluations`),
  re-run `make explain`, `make fairness`, `make report`, commit the new manifest and reports.
- **Rollback procedure:**
  1. `git checkout <previous-commit> -- models/manifest.json configs/base.yaml configs/models/`
  2. `make final` to rebuild the pipeline for that manifest (or restore the joblib from a local backup) and
     confirm `models/manifest.json: pipeline_sha256` matches `shasum -a 256 models/final_pipeline.joblib`.
  3. Restart the app; the version check passes only when config, manifest, and file agree.
  4. Record the rollback and reason in the deployment log (`docs/DEPLOYMENT.md` section 8).
- **Candidates:** tuned candidate pipelines are kept under `models/candidates/` (Git-ignored) so a different
  candidate can be promoted by re-running `select-model` with a documented rule change, never by editing results.

## 4. Continuous checks

`.github/workflows/ci.yml` runs on every push and pull request: `ruff check .`, the secrets scan (`make secrets`,
excluding recorded 40/64-hex checksums), `python -m ssn config validate`, `pytest -q` (tests needing the raw
dataset skip in CI), and the adviser-language scan over README, data docs, reports and the app package. The
test suite covers leakage (allow-list, fold isolation, parquet-read spies), privacy (no labels or sensitive
columns in adviser-facing outputs, forbidden imports in the app), metrics against hand-computed values,
artifact loading and checksum verification, and the acknowledgement flow.

## 5. Container

`docker build -t ssn .` copies `src/`, `configs/`, `models/`, `data/demo/`, `reports/` (only what the app reads),
`pyproject.toml`, `requirements.txt`; `.dockerignore` excludes `data/raw`, `data/processed`, `data/evaluation`,
`data/local`, `.env*`, `references/`, `.venv`, `.git`, tests, notebooks and specs (asserted by
`tests/unit/test_dockerignore.py`). Run with `docker run --rm -p 8050:8050 ssn`. The action log inside a container
is ephemeral by design; mount `data/local` as a volume to keep it.

## 6. Monitoring plan (what to watch, against which baseline)

The app computes nothing beyond scores; monitoring is a per-outreach-cycle checklist against baselines
already in the repository.

| Signal | Baseline (source) | Check each cycle |
|---|---|---|
| Score distribution / band shares | OOF band shares in `threshold_and_bands.json` (below) | share of records per band; a shift of the Priority band share by more than half its baseline is a flag |
| Input schema | `models/manifest.json: features.input_schema` | every incoming column present, codes within documented sets, no new columns (the app's validator does this per record) |
| List composition by group | `reports/fairness/group_metrics.json` selection rates at threshold (below) | recompute selection rate by gender and age band on the new list; compare to baseline; review the equal-opportunity gap whenever labels become available |
| Calibration | held-out ECE 0.034, Brier 0.118 (`models/manifest.json`) | when a cohort's outcomes become known, recompute reliability; re-calibrate if ECE roughly doubles |
| Ranking quality | held-out PR-AUC 0.817 (`models/manifest.json`) | recompute on the completed cohort; a drop below the CV lower bound (0.797) triggers re-training and a new audit |
| Adviser overrides | `data/local/actions.sqlite` | share of dismiss/override decisions; a rising share is a signal the model and adviser judgement are diverging |

Baseline band shares (out-of-fold, training split):

| Band | Score range | Share |
|---|---|---|
| Priority outreach | [0.9728, 1.0000] | 0.057 |
| Check-in suggested | [0.8412, 0.9728] | 0.056 |
| Standard support | [0.0000, 0.8412] | 0.887 |

Baseline selection rates and true-positive rates by group (held-out cohort, at threshold):

| Attribute | Group | n | Selection rate | TPR |
|---|---|---|---|---|
| gender | female | 575 | 0.0504 | 0.1986 |
| gender | male | 310 | 0.0903 | 0.1888 |
| age_band | 17-19 | 403 | 0.0199 | 0.1026 |
| age_band | 20-24 | 256 | 0.0352 | 0.1139 |
| age_band | 25-34 | 141 | 0.1348 | 0.2000 |
| age_band | 35+ | 85 | 0.2471 | 0.5000 |

Feedback-loop guard: adviser actions are never fed back into training; a retraining dataset would need to be
assembled deliberately, with the intervention recorded, and re-audited.

## 7. Open operational items

- Recording time of the three excluded financial-status columns (data owner question; `data/README.md`).
- Any pilot needs institutional approval, a local data agreement, re-training on local data, and a new fairness
  audit before the first cycle.
