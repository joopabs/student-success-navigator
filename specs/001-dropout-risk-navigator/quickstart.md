# Quickstart: Validate the Feature End-to-End

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Contracts**: [contracts/](contracts/)

This guide proves the feature works by running the documented commands and checking the
expected outcomes. It does not contain implementation code.

## Prerequisites

- Python 3.11, git, internet access for the one-time UCI download.
- Optional: `pandoc` (report export), `sqlite3` CLI (log inspection), Docker (M10).

## 1. Environment

```bash
git clone <repo-url> student-success-navigator && cd student-success-navigator
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m ssn config validate
```

Expected: exit 0; output lists `seed`, `capacity.k` with `illustrative: true`, and zero
allow-listed columns before M2, or the full allow-list afterwards.

## 2. Data acquisition and validation (M2)

```bash
make data          # download -> validate -> profile -> clean -> split
```

Expected:

- `data/raw/data.csv` present and sha256 matches `configs/base.yaml: data.expected_sha256`.
- `reports/tables/profile_target.csv` shows the three `Target` labels and the derived
  `is_dropout` balance (values come from the run, not from documentation).
- `configs/features.yaml` classifies every column; `pytest -q tests/unit/test_features_yaml_complete.py` passes.
- `data/demo/demo_cohort.parquet` contains no `Target`/`is_dropout`;
  `data/evaluation/demo_cohort_labels.parquet` contains only `record_id`, `is_dropout`, `Target`.
- `git status` shows no files under `data/raw`, `data/processed`, `data/demo`, `data/evaluation`.

## 3. Leakage gate (G3)

```bash
pytest -q tests/unit/test_allowlist.py tests/unit/test_split.py tests/unit/test_engineering.py
```

Expected: all pass. Manually confirm the negative case:

```bash
python - <<'PY'
import pandas as pd
from ssn.features.allowlist import assert_frame_allowed, LeakageError
df = pd.read_parquet('data/processed/train.parquet')
try:
    assert_frame_allowed(df)          # train still carries is_dropout -> must raise
    raise SystemExit("FAIL: label column accepted")
except LeakageError as e:
    print("OK leakage guard raised:", e)
PY
```

## 4. EDA, selection, PCA (M3-M4)

```bash
make eda && make select && python -m ssn pca
```

Expected: figures under `reports/figures/`, `selection_decision.json`, `pca_vs_nopca_cv.csv`.
Any second-semester plot is named `analysis_only_*`.

## 5. Model comparison, tuning, final fit, single test evaluation (M5-M6)

```bash
make cv && make tune && make final
cat reports/tables/cv_comparison.csv
cat reports/tables/selection_matrix.csv
python -c "import json;m=json.load(open('models/manifest.json'));print(m['model_version'], m['test_evaluations'], m['threshold'])"
```

Expected:

- `cv_comparison.csv` has rows for `dummy`, `logreg`, `random_forest`, `hist_gb` with mean/std.
- `selection_matrix.csv` has no `accuracy` column.
- `manifest.json` has `test_evaluations: 1`, non-placeholder `test_summary`, threshold and
  bands filled, `capacity_illustrative: true`.
- `models/final_pipeline.joblib` exists and its sha256 equals `manifest.pipeline_sha256`.

## 6. Reproducibility (G9)

```bash
rm -rf .venv && python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
make all
python -m ssn reproduce-check
```

Expected: `docs/REPRODUCIBILITY.md` table shows per-metric deltas within the recorded tolerance.

## 7. Explainability and fairness (M7)

```bash
make explain && make fairness && python -m ssn model-card
python -c "import json;g=json.load(open('reports/fairness/group_metrics.json'));print([(r['attribute'],r['group'],r['n'],r['reliable']) for r in g['groups']])"
```

Expected: SHAP and PDP/ICE figures under `reports/explainability/`; every group row has `n`
and `reliable`; `reports/model_card.md` renders with no placeholder values; `fairness audit`
refuses to run if the gender encoding is not marked verified in `data/data_dictionary.md`.

## 8. Language and labelling scan (G8, SC-008, SC-011)

```bash
python -m ssn scan-language --paths src/ssn/app reports README.md docs
```

Expected: exit 0 with zero findings.

## 9. Application (M9)

```bash
pytest -q tests/app
python -m ssn app
```

Open http://127.0.0.1:8050 and verify:

- `/`: disclaimer, illustrative K label, model version.
- `/queue`: exactly K rows (or full cohort with notice), no outcome column, "Record support
  action" opens a modal whose Save button is disabled until the acknowledgement box is checked.
- `/review/<id>`: neutral factor phrases; no gender or age as a reason.
- `/score`: submitting an out-of-range value yields a field-level message and no score.
- `/equity`: groups with `n` and warnings for small groups.
- `/model-card`: intended use, non-use, citation, metrics, limitations.

Then:

```bash
sqlite3 data/local/actions.sqlite 'select count(*), min(logged_at_utc) from support_actions;'
git check-ignore -v data/local/actions.sqlite
```

Expected: rows equal the actions you recorded; the file is ignored.

Version-mismatch check: set `app.expected_model_version` to a different value in a copy of the
config, start the app with `--config` pointing at it, and confirm a blocking message with no
scores.

## 10. Report and decks (M8)

```bash
python -m ssn rubric-map
jupyter nbconvert notebooks/90_technical_deck.ipynb --to slides --output-dir reports/decks
```

Expected: `reports/rubric_map.md` links every rubric criterion; technical deck has 8-12 slides;
`reports/decks/business_deck_outline.md` records the business deck slide count (8-12) and the
KPI value read from `reports/tables/test_recall_precision_at_k.csv` with an "illustrative" label.

## 11. Pre-publication checklist

```bash
git ls-files | grep -Ei 'data/(raw|processed|demo|evaluation|local)/|\.env$|\.sqlite|Pillar5' && echo "STOP: private file tracked" || echo "clean"
pytest -q && ruff check .
```

Expected: `clean`, all tests pass, lint clean. Only then make the repository public.
