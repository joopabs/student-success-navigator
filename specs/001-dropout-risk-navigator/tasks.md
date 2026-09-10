---

description: "Task list for Fair and Explainable Student Dropout Risk Prediction and Student Success Navigator"
---

# Tasks: Fair and Explainable Student Dropout Risk Prediction for Early Academic Support

**Input**: Design documents from `/specs/001-dropout-risk-navigator/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md,
`.specify/memory/constitution.md` v1.0.0

**Tests**: Included. The specification (FR-055) and constitution (Principle IV, gates G3/G8/G9)
require automated tests for leakage, privacy, metrics, and app safeguards.

**Organization**: Phases follow the ten implementation milestones requested by the user and
defined in plan.md. Phase 1 (scaffold) and Phase 2 (data foundation) carry no story label.
Every task from Phase 3 onward carries the user-story label it serves so stories remain
traceable:

| Story | Title (spec.md) | Priority |
|-------|-----------------|----------|
| US1 | Build a leakage-safe, comparable support-priority model | P1 |
| US2 | Prioritise weekly voluntary outreach from the Support Queue | P1 |
| US3 | Review an individual record with neutral explanations | P2 |
| US4 | Audit equity of model behaviour across student groups | P2 |
| US5 | Score a hypothetical new record | P3 |
| US6 | Consume the report, decks, and model card | P3 |

**Empirical-claims rule**: Tasks marked `Type: run` execute the pipeline on real data. No
report, notebook, README, deck, or model card may state a count, metric, encoding, or fairness
value until the corresponding `run` task has produced it in a file under `reports/`, `models/`,
or `data/`. Until then, write the placeholder `[PENDING: <artifact path>]`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: User story served (US1-US6); omitted in Phases 1-2
- Each task is followed by an indented block: Type, Deps, Accept (acceptance criteria), Verify
  (commands). Types: `code`, `tests`, `config`, `docs`, `notebook`, `reports`, `artifacts`,
  `run`.

## Path Conventions

Single project at repository root: `src/ssn/` (package), `tests/`, `configs/`, `data/`,
`models/`, `reports/`, `notebooks/`, `docs/`. Full tree in plan.md.

---

## Phase 1: Scaffold and Environment (Milestone 1)

**Purpose**: Importable package, validated configuration, quality tooling, leakage and language
guards in place before any data is touched.

- [X] T001 Create the directory skeleton with `.gitkeep` files per plan.md: `src/ssn/{data,features,modeling,explain,fairness,reporting,app/{services,components,pages}}`, `tests/{unit,integration,app}`, `configs/models`, `data/{raw,processed,demo,evaluation,local}`, `models`, `reports/{figures,tables,explainability,fairness,decks}`, `notebooks`, `docs`
  - Type: artifacts
  - Deps: none
  - Accept: every directory exists; `git status` shows only `.gitkeep` files and no data files
  - Verify: `find src tests configs data models reports notebooks docs -type d | sort` and `git status --short`
- [X] T002 Write `pyproject.toml` (package `ssn`, `src` layout, ruff and pytest config, Python `>=3.11,<3.12`), `.python-version` (`3.11`), `requirements.txt` (pinned: pandas, numpy, scikit-learn >= 1.4 for `HistGradientBoostingClassifier(class_weight=...)`, imbalanced-learn, shap >= 0.45 for HistGradientBoosting support in `TreeExplainer`, matplotlib, seaborn, joblib, PyYAML, pyarrow, dash, plotly), `requirements-dev.txt` (pytest, pytest-cov, ruff, nbconvert, jupyter, detect-secrets)
  - Type: config
  - Deps: T001
  - Accept: fresh venv installs both files without resolver errors; a smoke check fits `HistGradientBoostingClassifier(class_weight='balanced')` on a toy array and constructs `shap.TreeExplainer` on it without error; `python -c "import ssn"` fails only because the package has no code yet
  - Verify: `python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt && pip check`
- [X] T003 [P] Write `Makefile` with targets `setup, data, eda, select, cv, tune, final, explain, fairness, report, app, test, lint, all` that call `python -m ssn ...` exactly as listed in contracts/cli.md
  - Type: config
  - Deps: T001
  - Accept: `make -n <target>` prints the intended commands for every target; no target references a command absent from contracts/cli.md
  - Verify: `for t in setup data eda select cv tune final explain fairness report app test lint all; do make -n $t >/dev/null || echo "missing $t"; done`
- [X] T004 [P] Extend `.gitignore` with `data/raw/*`, `!data/raw/.gitkeep`, `data/processed/`, `data/demo/`, `data/evaluation/`, `data/local/`, `models/*.joblib` (policy per research R-11), and write `.env.example` with no real values
  - Type: config
  - Deps: T001
  - Accept: `git check-ignore` returns a match for a sample path in each ignored directory; `.env.example` is tracked
  - Verify: `for p in data/raw/data.csv data/processed/x.parquet data/demo/x.parquet data/evaluation/x.parquet data/local/actions.sqlite models/final_pipeline.joblib; do git check-ignore -q $p && echo "ignored $p" || echo "NOT IGNORED $p"; done`
- [X] T005 [P] Write `README.md` skeleton with one heading per rubric criterion from `CAPSTONE_BRIEF.md` Section 5, a "Reproduction" section, a "Repository structure" section, and `[PENDING: ...]` placeholders for every number
  - Type: docs
  - Deps: T001
  - Accept: headings for Steps 1-7, Bonus, Reproduction, Structure exist; zero numeric claims outside placeholders
  - Verify: `grep -c '^## ' README.md` and `grep -n 'PENDING' README.md`
- [X] T006 Write `configs/base.yaml` exactly per contracts/config-schema.md with `seed: 42`, `capacity.per_week: 10`, `capacity.window_weeks: 5`, `capacity.k: 50`, `capacity.window_sensitivity_weeks: [2, 5, 10]`, `capacity.illustrative: true`, `fairness.min_group_size: 30`, `fairness.age_bands: []`, `data.expected_sha256: ""`, `project.model_version: "1.0.0"`, `app.expected_model_version: "1.0.0"`
  - Type: config
  - Deps: T001
  - Accept: file parses as YAML; all keys in the contract present; illustrative flag true; `k == per_week * window_weeks`
  - Verify: `python -c "import yaml;c=yaml.safe_load(open('configs/base.yaml'))['capacity'];assert c['illustrative'] is True and c['k']==c['per_week']*c['window_weeks'];print(c)"`
- [X] T007 [P] Write `configs/features.yaml` skeleton with empty `columns: []` and `engineered: []` lists, and `configs/language.yaml` with the `prohibited_terms` list from research R-18 and an empty `features:` map
  - Type: config
  - Deps: T001
  - Accept: both parse; prohibited terms include "at risk of failing", "likely to drop out", "problem student", "failing student"
  - Verify: `python -c "import yaml;l=yaml.safe_load(open('configs/language.yaml'));print(l['prohibited_terms'])"`
- [X] T008 [P] Write `configs/models/dummy.yaml`, `logreg.yaml`, `random_forest.yaml`, `hist_gb.yaml` per contracts/config-schema.md (estimator class path, `class_weight: balanced` where supported, `random_state: ${seed}`, search spaces, `n_iter`, `use_selection`, `use_pca`)
  - Type: config
  - Deps: T001
  - Accept: four files; dummy has no search space; each non-dummy has a non-empty `search_space`
  - Verify: `python -c "import yaml,glob;[print(f, sorted(yaml.safe_load(open(f)))) for f in sorted(glob.glob('configs/models/*.yaml'))]"`
- [X] T009 Implement `src/ssn/__init__.py` (version string), `src/ssn/__main__.py`, `src/ssn/paths.py`, and `src/ssn/cli.py` with an argparse subcommand registry, `--config` and `--log-level` global options, and exit codes 0/2/3/4 per contracts/cli.md; register stubs for every command that exit 2 with "not implemented" until wired
  - Type: code
  - Deps: T002
  - Accept: `python -m ssn --help` lists every command in contracts/cli.md; unknown command exits non-zero
  - Verify: `python -m ssn --help` and `python -m ssn nope; echo "exit=$?"`
- [X] T010 Implement `src/ssn/config.py`: load YAML, validate required keys and types against contracts/config-schema.md, raise `ConfigError` naming the key path, substitute `${seed}` in model configs, seed `random` and `numpy`, return a frozen dataclass; wire `config validate`
  - Type: code
  - Deps: T006, T009
  - Accept: valid config prints resolved seed and illustrative flags; a config missing `capacity.illustrative` exits 2 with the key path in the message
  - Verify: `python -m ssn config validate` and `python - <<'PY'
import yaml,subprocess,tempfile
c=yaml.safe_load(open('configs/base.yaml')); del c['capacity']['illustrative']
p=tempfile.NamedTemporaryFile('w',suffix='.yaml',delete=False); yaml.safe_dump(c,p); p.close()
r=subprocess.run(['python','-m','ssn','config','validate','--config',p.name],capture_output=True,text=True); print(r.returncode, r.stderr.strip()[:120]); assert r.returncode==2
PY`
- [X] T011 Write `tests/conftest.py` with a small synthetic fixture DataFrame (about 60 rows, invented column names mirroring the availability classes, both target classes, no real rows) plus a fixture `features.yaml` written to `tmp_path`; write `tests/unit/test_config.py` covering valid load, missing key, wrong type, and seed substitution
  - Type: tests
  - Deps: T010
  - Accept: fixture is deterministic (seeded); tests pass
  - Verify: `pytest -q tests/unit/test_config.py`
- [X] T012 Implement `src/ssn/features/allowlist.py`: load `features.yaml`, derive `allowed`, `prohibited`, `sensitive`, `unclassified` sets, `project_features(df)` returning only allow-listed columns, `assert_frame_allowed(X)` raising `LeakageError` naming offending columns, and `assert_all_classified(raw_columns)`; write `tests/unit/test_allowlist.py` for projected frame passes, full frame with label raises, prohibited column raises, unclassified column raises, sensitive column raises
  - Type: code, tests
  - Deps: T007, T011
  - Accept: all five cases tested; error message lists column names; `project_features` drops label and sensitive columns
  - Verify: `pytest -q tests/unit/test_allowlist.py`
- [X] T013 Implement `src/ssn/explain/language.py`: load `language.yaml`, `scan_text(text)` returning prohibited-term hits, `scan_paths(paths)` over `.py/.md/.yaml/.ipynb`, detection of a currency or percent figure within a paragraph containing "ROI", "saving", "value", or "capacity" but lacking "illustrative" or "assumption", and the bare phrase "the model is fair"; wire `scan-language` (exit 1 on findings); write `tests/unit/test_language.py`
  - Type: code, tests
  - Deps: T007, T009
  - Accept: scanner flags each rule on crafted strings and passes on clean text; CLI exits 1 on findings
  - Verify: `pytest -q tests/unit/test_language.py && python -m ssn scan-language --paths README.md; echo "exit=$?"`
- [X] T014 Run the quality gate for Phase 1: lint, tests, CLI help, and the tracked-file privacy check
  - Type: run
  - Deps: T003, T004, T005, T008, T012, T013
  - Accept: ruff clean, all tests pass, no private files tracked
  - Verify: `ruff check . && pytest -q && git ls-files | grep -Ei 'data/(raw|processed|demo|evaluation|local)/.*\.(csv|parquet|sqlite)$|\.env$|Pillar5' && echo LEAK || echo clean`

**Checkpoint**: Package installs, config validates, leakage and language guards exist and are
tested. No data has been downloaded.

---

## Phase 2: Data Acquisition, Schema Validation, Profiling, and Data Dictionary (Milestone 2)

**Purpose**: Establish provenance, verify the dataset, classify every column by availability,
and record every empirical fact about the raw data from computed output. BLOCKS all stories.

- [X] T015 Implement `src/ssn/data/download.py` and wire `data download`: fetch the UCI dataset 697 archive, extract `data.csv` to `configs.paths.raw_csv`, compute sha256, compare to `data.expected_sha256` (on empty expected value, print the hash and exit 2 with instruction to record it), refuse on mismatch
  - Type: code
  - Deps: T010
  - Accept: first run prints the hash; after recording it in `configs/base.yaml`, second run succeeds and is idempotent
  - Verify: `python -m ssn data download; echo "exit=$?"` then record hash, then `python -m ssn data download && shasum -a 256 data/raw/data.csv`
- [X] T016 Implement `src/ssn/data/schema.py` and wire `data validate`: load raw CSV, assert every column is classified (via `allowlist.assert_all_classified`), infer and check dtypes, assert observed `Target` values equal `data.target_expected_labels` exactly, write `reports/tables/validate_report.json` (columns, dtypes, target labels observed, row count)
  - Type: code
  - Deps: T012, T015
  - Accept: with the empty `features.yaml` skeleton the command exits 2 listing all unclassified columns; the report JSON is still written with observed facts
  - Verify: `python -m ssn data validate; echo "exit=$?"; python -c "import json;print(json.load(open('reports/tables/validate_report.json'))['n_rows'])"`
- [X] T017 Implement `src/ssn/data/profile.py` and wire `data profile`: per-column dtype, n_missing, n_unique, min, max, top values for categoricals; `Target` frequencies and derived `is_dropout` balance; exact-duplicate count; write `reports/tables/profile_columns.csv`, `profile_target.csv`, `profile_duplicates.csv`, `profile_categorical_values.csv`, and `configs/ranges.json` (observed min/max per numeric column for later app validation)
  - Type: code
  - Deps: T015
  - Accept: all five outputs written; `ranges.json` keys equal numeric column names
  - Verify: `python -m ssn data profile && ls reports/tables/profile_*.csv configs/ranges.json`
- [X] T018 Run `data download`, `data profile`, and `data validate` on the real file and record PV-01 (row and column counts, column names), PV-02 (`Target` values and `is_dropout` balance), and PV-05 (missing, duplicates, ranges) in `data/README.md` under "Profiling results (computed <date>)" by pasting from the CSV outputs
  - Type: run, docs
  - Deps: T016, T017
  - Accept: every number in the README section matches the CSV files; the `validate` exit code and unclassified-column list are recorded for T019
  - Verify: `python -m ssn data download && python -m ssn data profile && python -m ssn data validate; cat reports/tables/profile_target.csv`
- [X] T019 Fill `configs/features.yaml` with one entry per observed column (from `validate_report.json`): `availability`, `role`, `dtype`, `adviser_visible`, `encoding_source`, `encoding_verified: false`, `note` citing the UCI variables table or the source article; classify every second-semester column as `second_semester`, `Target` as `outcome`/`target`, the sensitive set from `PROJECT_DECISIONS.md` (gender, age at enrollment, nationality, international status, marital status, educational special needs) as `role: sensitive`, and financial-status columns as `ambiguous` per research R-05 unless documentation confirms first-semester availability
  - Type: config
  - Deps: T018
  - Accept: `data validate` exits 0; counts of allowed, prohibited, ambiguous, and sensitive columns printed and recorded in `data/README.md` (PV-03)
  - Verify: `python -m ssn data validate && python -c "from ssn.features.allowlist import load;a=load('configs/features.yaml');print(len(a.allowed),len(a.prohibited),len(a.ambiguous),len(a.sensitive))"`
- [X] T020 Verify categorical encodings (PV-04): for each categorical column compare `reports/tables/profile_categorical_values.csv` against the UCI variables table (https://archive.ics.uci.edu/dataset/697) and the source article (Realinho et al., 2022, *Data* 7(11):146); set `encoding_verified: true` only where observed codes match documented codes; record the gender code mapping and any discrepancy in `data/data_dictionary.md` under "Encoding verification". Escalation if gender codes cannot be verified from the UCI variables table: check the source article's variable description; if still unverified, keep `encoding_verified: false`, record the blocker in `data/README.md` under "Open verification items", and open a constitution amendment proposal before Phase 7, because Principle X requires gender to be assessed. Never infer the mapping from class distributions
  - Type: docs, config
  - Deps: T019
  - Accept: gender has `encoding_verified: true` or an explicit "unverified, fairness audit blocked" note; every categorical column has a verification status
  - Verify: `python -c "import yaml;c=yaml.safe_load(open('configs/features.yaml'))['columns'];print([(x['name'],x['encoding_verified']) for x in c if x['dtype']=='categorical'])"`
- [X] T021 Implement `src/ssn/reporting/tables.py::write_data_dictionary` and wire it into `data profile`: generate `data/data_dictionary.md` with one row per source column (name, type, availability, role, allowed values or observed range, encoding source, verified flag, description) plus a section for engineered features to be appended in Phase 3; preserve a hand-written "Notes" section across regenerations
  - Type: code, docs
  - Deps: T019
  - Accept: dictionary regenerates without losing the Notes section; every column from `validate_report.json` appears
  - Verify: `python -m ssn data profile && grep -c '^|' data/data_dictionary.md`
- [X] T022 [P] Write `tests/unit/test_schema.py` (fixture CSV: wrong Target label fails, missing column fails, extra column fails) and `tests/unit/test_features_yaml_complete.py` (every fixture column classified exactly once; `ambiguous`, `second_semester`, `outcome` excluded from allowed; sensitive never allowed)
  - Type: tests
  - Deps: T016, T019
  - Accept: tests pass on fixture and on the real `configs/features.yaml`
  - Verify: `pytest -q tests/unit/test_schema.py tests/unit/test_features_yaml_complete.py`
- [X] T023 [P] Write `tests/integration/test_profile_fixture.py`: run `profile` functions on the synthetic fixture and assert output tables have expected columns and counts
  - Type: tests
  - Deps: T017
  - Accept: passes without touching `data/raw`
  - Verify: `pytest -q tests/integration/test_profile_fixture.py`
- [X] T024 [P] Create `notebooks/01_data_profiling.ipynb` that imports `ssn.data.profile`, displays the profile tables and target balance from files, and shows `head()` of de-identified columns only; execute top-to-bottom
  - Type: notebook
  - Deps: T018
  - Accept: executes cleanly from a fresh kernel; no code duplicated from `src/`
  - Verify: `jupyter nbconvert --to notebook --execute notebooks/01_data_profiling.ipynb --output /tmp/01.ipynb`
- [X] T025 Complete `data/README.md`: dataset name, UCI URL, DOI 10.24432/C5MC89, recommended citation (verbatim from research R-01), licence CC BY 4.0 with link, access date, sha256, download steps, single-institution and non-generalisation statement, and PV-09 confirmation that licence terms were read
  - Type: docs
  - Deps: T018
  - Accept: all fields present; citation text matches research R-01; no claim of Philippine or general representativeness
  - Verify: `grep -nE 'CC BY 4.0|10.24432/C5MC89|sha256|Realinho' data/README.md`

**Checkpoint**: Every raw column is classified and every fact about the raw data is computed
and recorded. User story work can begin.

---

## Phase 3: Cleaning, EDA, and Leakage-Safe Feature Engineering (Milestone 3) — US1

**Goal**: Produce clean, split, engineered, leakage-safe datasets and an EDA report built from
computed tables and figures.

**Independent Test**: `make data && make eda` regenerates train/test/demo/evaluation files and
figures; `pytest -q tests/unit/test_split.py tests/unit/test_engineering.py` passes; the demo
cohort has no label columns.

- [X] T026 [US1] Implement `src/ssn/data/clean.py` and wire `data clean`: handle missing values, exact duplicates, invalid or out-of-range values (using `configs/ranges.json` and documented allowed codes), and flag outliers per a documented rule; write `data/processed/clean.parquet` and `reports/tables/clean_before_after.csv` (issue, column, count_before, count_after, treatment)
  - Type: code
  - Deps: T019, T021
  - Accept: before/after table has one row per issue-column pair; treatment strings are non-empty
  - Verify: `python -m ssn data clean && head -20 reports/tables/clean_before_after.csv`
- [X] T027 [US1] Implement `src/ssn/data/split.py` and wire `data split`: derive `is_dropout` per research R-04, add seeded synthetic `record_id`, stratified train/test split per config, write `data/processed/train.parquet`, `data/processed/test.parquet`, `data/demo/demo_cohort.parquet` (record_id + allow-listed feature columns only; no `Target`, `is_dropout`, or `role: sensitive` columns), `data/evaluation/demo_cohort_labels.parquet` (record_id, is_dropout, Target, sensitive columns); write `reports/tables/split_summary.csv` (sizes, positive rates)
  - Type: code
  - Deps: T026
  - Accept: demo cohort lacks label and sensitive columns; train/test disjoint by `record_id`; split summary written
  - Verify: `python -m ssn data split && python -c "import pandas as pd;from ssn.features.allowlist import load;a=load('configs/features.yaml');d=pd.read_parquet('data/demo/demo_cohort.parquet');assert not ({'Target','is_dropout'}|set(a.sensitive))&set(d.columns);print(d.shape)"`
- [X] T028 [US1] Implement `src/ssn/features/engineering.py` as a scikit-learn transformer that declares its input columns (`get_input_columns()`), computes `sem1_approval_rate`, `sem1_evaluation_participation_rate`, `sem1_non_evaluation_rate`, `grade_diff_vs_admission`, `age_band` (from `config.fairness.age_bands`; passthrough NaN when bands are empty; produced for EDA and auditing only and excluded from the model feature list because its input is `role: sensitive`), and documented workload/progression measures; apply the zero-denominator rule (NaN then impute, count logged to `reports/tables/zero_denominators.csv`); append engineered entries to `configs/features.yaml`
  - Type: code, config
  - Deps: T027
  - Accept: every engineered feature's inputs are allow-listed; zero-denominator counts written; `features.yaml` `engineered` list populated
  - Verify: `python -c "from ssn.features.engineering import Sem1FeatureEngineer as E;print(E().get_input_columns())"`
- [X] T029 [US1] Implement `src/ssn/features/preprocess.py::build_preprocessor(cfg, allowlist)`: `ColumnTransformer` with numeric imputation and scaling, categorical one-hot with unknown handling, engineered features inserted via the transformer from T028, and `get_feature_names_out` support
  - Type: code
  - Deps: T028
  - Accept: fits on the synthetic fixture and transforms without error; feature names recoverable
  - Verify: `pytest -q tests/unit/test_engineering.py -k preprocess` (after T030)
- [X] T030 [P] [US1] Write `tests/unit/test_clean.py` (each treatment applied on fixture; counts logged), `tests/unit/test_split.py` (no label or `role: sensitive` columns in demo; sensitive columns present in evaluator file; disjoint ids; stratification within tolerance; synthetic id not row index), `tests/unit/test_engineering.py` (inputs allow-listed; zero-denominator rule; `preprocess` names)
  - Type: tests
  - Deps: T026, T027, T029
  - Accept: all pass on fixture
  - Verify: `pytest -q tests/unit/test_clean.py tests/unit/test_split.py tests/unit/test_engineering.py`
- [X] T031 [US1] Implement `src/ssn/reporting/figures.py` and wire `eda`: univariate distributions, target relationships, correlation heatmap, age distribution, engineered-feature distributions, all from `train.parquet`; any second-semester plot reads raw data in an isolated function and saves as `reports/figures/analysis_only_*.png`; write `reports/tables/eda_summary.csv`
  - Type: code
  - Deps: T028
  - Accept: figures saved; no second-semester column is read outside the analysis-only function (grep)
  - Verify: `python -m ssn eda && ls reports/figures | head -30`
- [X] T032 [US1] Run `data clean`, `data split`, `eda` on real data and record: cleaning before/after counts, train/test sizes and positive rates, zero-denominator counts (PV-08), age distribution summary (PV-06 input) into `reports/tables/` outputs and `data/README.md`
  - Type: run
  - Deps: T030, T031
  - Accept: all listed tables exist and are non-empty; README cites file paths for each number
  - Verify: `make data && make eda && cat reports/tables/split_summary.csv reports/tables/zero_denominators.csv`
- [X] T033 [US1] Decide age-band boundaries from the computed age distribution (PV-06): choose bands keeping each above `min_group_size` where possible, write them into `configs/base.yaml: fairness.age_bands`, and record the rationale in `data/data_dictionary.md`; re-run `data split` and `eda` so `age_band` is populated
  - Type: config, run
  - Deps: T032
  - Accept: `age_bands` non-empty; band counts in `reports/tables/eda_summary.csv`; rationale references the age summary table
  - Verify: `python -c "import yaml;print(yaml.safe_load(open('configs/base.yaml'))['fairness']['age_bands'])" && make data && make eda`
- [X] T034 [P] [US1] Create `notebooks/02_eda_feature_engineering.ipynb`: import `ssn` functions, display cleaning table, figures, engineered-feature rationale, and an "analysis-only" section for second-semester plots; execute top-to-bottom
  - Type: notebook
  - Deps: T032
  - Accept: executes; analysis-only section clearly titled
  - Verify: `jupyter nbconvert --to notebook --execute notebooks/02_eda_feature_engineering.ipynb --output /tmp/02.ipynb`
- [X] T035 [US1] Write `reports/eda_feature_engineering_report.md`: data-quality treatments with before/after counts (from CSV), imbalance quantification, EDA findings referencing figure files, engineered features with one-line academic rationale each, zero-denominator handling, and an "Ambiguous columns" section noting the ablation is pending Phase 5
  - Type: reports
  - Deps: T033
  - Accept: every number traces to a file in `reports/tables/`; `scan-language` passes
  - Verify: `python -m ssn scan-language --paths reports/eda_feature_engineering_report.md`

**Checkpoint**: Leakage-safe datasets and EDA report exist; demo cohort carries no labels.

---

## Phase 4: Feature Selection and PCA (Milestone 4) — US1

**Goal**: Train-only filter and embedded selection and a PCA comparison, all fitted inside
cross-validation.

**Independent Test**: `make select && python -m ssn pca` writes decision JSON and comparison
tables; `pytest -q tests/unit/test_selection_in_pipeline.py tests/unit/test_pca_fit_isolation.py`
passes.

- [X] T036 [US1] Implement `src/ssn/modeling/cv.py`: `make_cv(cfg)` (StratifiedKFold, seeded), `oof_predict(pipeline, X, y, cv)` returning fold ids and scores, and `k_for_fold(k, n_fold, n_test_expected)` per research R-08
  - Type: code
  - Deps: T029
  - Accept: unit-tested rounding of `k_for_fold`; OOF covers every row once
  - Verify: `pytest -q tests/unit/test_metrics.py -k k_for_fold` (after T042) or `python -c "from ssn.modeling.cv import k_for_fold;print(k_for_fold(50,177,885))"`
- [X] T037 [US1] Implement `src/ssn/modeling/selection.py` (filter step: `SelectKBest` with mutual information or ANOVA F; embedded step: `SelectFromModel` with L1 logistic regression or tree importances, both as pipeline steps configurable from `selection.*`) and wire `select`: run CV over `k_grid`, write `reports/tables/selection_filter_scores.csv`, `selection_embedded_scores.csv`, `selection_cv_by_k.csv`, `selection_decision.json`
  - Type: code
  - Deps: T036
  - Accept: selectors are pipeline steps (never fit outside CV); decision JSON names the method and chosen k
  - Verify: `python -m ssn select && cat reports/tables/selection_decision.json`
- [X] T038 [US1] Implement `src/ssn/modeling/pca.py` and wire `pca`: pipeline `preprocessor -> PCA(n_components=variance_threshold) -> logistic regression` compared against the non-PCA pipeline under CV; write `reports/tables/pca_explained_variance.csv`, `pca_vs_nopca_cv.csv`, `reports/figures/pca_scree.png`, `reports/figures/pca_2d_train.png` (train only, coloured by `is_dropout`)
  - Type: code
  - Deps: T036
  - Accept: PCA fitted only inside folds; 2D plot uses train only
  - Verify: `python -m ssn pca && cat reports/tables/pca_vs_nopca_cv.csv`
- [X] T039 [P] [US1] Write `tests/unit/test_selection_in_pipeline.py` (selector inside `Pipeline`; validation-fold rows do not change fitted mask) and `tests/unit/test_pca_fit_isolation.py` (PCA components identical with and without extra test rows present in the frame passed to `cross_validate` on train indices; `select`/`pca` read only train path via monkeypatched `read_parquet`)
  - Type: tests
  - Deps: T037, T038
  - Accept: pass on fixture
  - Verify: `pytest -q tests/unit/test_selection_in_pipeline.py tests/unit/test_pca_fit_isolation.py`
- [X] T040 [US1] Run `select` and `pca` on real train data; record chosen method, k, and the PCA versus non-PCA CV result in `reports/tables/` and summarise (with file references) in `reports/eda_feature_engineering_report.md` under "Feature selection" and "Dimensionality reduction"
  - Type: run, reports
  - Deps: T039
  - Accept: report cites `selection_decision.json` and `pca_vs_nopca_cv.csv`; PCA retained or not with reason
  - Verify: `make select && python -m ssn pca && python -m ssn scan-language --paths reports/eda_feature_engineering_report.md`
- [X] T041 [P] [US1] Create `notebooks/03_feature_selection_pca.ipynb` displaying selection scores, CV-by-k curve, scree plot, 2D projection; execute top-to-bottom
  - Type: notebook
  - Deps: T040
  - Accept: executes; imports from `ssn`
  - Verify: `jupyter nbconvert --to notebook --execute notebooks/03_feature_selection_pca.ipynb --output /tmp/03.ipynb`

**Checkpoint**: Selection and PCA decisions are computed and justified.

---

## Phase 5: Baseline and Candidate Model Comparison (Milestone 5) — US1

**Goal**: Dummy baseline plus logistic regression, random forest, and HistGradientBoosting
compared under identical CV with PR-AUC, Recall@K, Precision@K, calibration, and imbalance
treatment comparison.

**Independent Test**: `make cv` writes `cv_comparison.csv` with four model rows and OOF files;
`pytest -q tests/unit/test_metrics.py tests/integration/test_cv_fixture.py` passes.

- [X] T042 [US1] Implement `src/ssn/modeling/evaluate.py`: `pr_auc`, `roc_auc`, `recall_at_k`, `precision_at_k`, `brier`, `expected_calibration_error(n_bins=10)`, `confusion_at_threshold`, `metrics_table(y, score, threshold, k)`; write `tests/unit/test_metrics.py` with hand-computed expectations on tiny arrays including ties at the K boundary
  - Type: code, tests
  - Deps: T036
  - Accept: every metric tested against a hand-computed value; tie handling deterministic
  - Verify: `pytest -q tests/unit/test_metrics.py`
- [X] T043 [US1] Implement `src/ssn/modeling/candidates.py::build_pipeline(name, cfg, allowlist)`: read `configs/models/<name>.yaml`, compose preprocessor, optional selector, optional PCA, optional `imblearn` SMOTENC step with categorical column indices (when `imbalance.compare_smote`), estimator with seed; write `tests/unit/test_candidates_build.py` (each of four names builds; SMOTENC variant uses `imblearn.pipeline.Pipeline` and receives the correct categorical indices)
  - Type: code, tests
  - Deps: T037, T038
  - Accept: four pipelines build from fixture; `random_state` equals config seed
  - Verify: `pytest -q tests/unit/test_candidates_build.py`
- [X] T044 [US1] Wire `train-cv --models ...`: always include `dummy`; for each model and imbalance variant run CV, save OOF to `data/processed/oof_<model>[_smote].parquet`, write `reports/tables/cv_comparison.csv` (mean/std per metric incl. accuracy for transparency, fit_time_s) and `reports/figures/cv_pr_curves.png`; add `--ablation ambiguous` and `--ablation sensitive` flags that additionally run the models with, respectively, `ambiguous` columns promoted and `role: sensitive` columns temporarily included, writing `reports/tables/ablation_ambiguous.csv` and `reports/tables/ablation_sensitive.csv` (the sensitive ablation is analysis-only and never persisted as a candidate)
  - Type: code
  - Deps: T042, T043
  - Accept: command reads only train parquet; dummy row present; ablation table produced when flag set
  - Verify: `python -m ssn train-cv --models dummy logreg random_forest hist_gb --ablation ambiguous --ablation sensitive && cat reports/tables/cv_comparison.csv`
- [X] T045 [P] [US1] Write `tests/integration/test_cv_fixture.py`: run `train-cv` logic on the synthetic fixture; assert validation fold sizes unchanged by SMOTE, OOF covers all rows once, output columns present, test path never read (monkeypatch)
  - Type: tests
  - Deps: T044
  - Accept: passes in under 60 seconds
  - Verify: `pytest -q tests/integration/test_cv_fixture.py`
- [X] T046 [US1] Run `train-cv` on real train data for all four models with the SMOTENC comparison, the ambiguous-column ablation, and the sensitive-attribute ablation; record results in `reports/tables/cv_comparison.csv`, `ablation_ambiguous.csv`, and `ablation_sensitive.csv`; summarise the performance cost of excluding sensitive attributes (with file reference) in the EDA report and later the Bias & Fairness Analysis; add the ablation conclusion (include or exclude ambiguous columns, with numbers referenced) to `reports/eda_feature_engineering_report.md` and, if promoting any column, update `configs/features.yaml` with a `note` citing the documentation and re-run Phases 3-5
  - Type: run, reports
  - Deps: T045
  - Accept: tables exist; ablation decision recorded with file reference; imbalance-treatment choice recorded per research R-07
  - Verify: `make cv && cat reports/tables/ablation_ambiguous.csv`
- [X] T047 [P] [US1] Create `notebooks/04_model_comparison.ipynb` displaying `cv_comparison.csv`, PR curves, SMOTE versus class-weight comparison, and ablation table; execute top-to-bottom
  - Type: notebook
  - Deps: T046
  - Accept: executes; no metric typed by hand
  - Verify: `jupyter nbconvert --to notebook --execute notebooks/04_model_comparison.ipynb --output /tmp/04.ipynb`

**Checkpoint**: Four models compared on identical folds with computed tables.

---

## Phase 6: Tuning, Threshold/Capacity Analysis, Final Evaluation, and Artifacts (Milestone 6) — US1 (+US4 metrics)

**Goal**: Tune candidates, select by multi-criteria matrix, derive capacity-aware threshold and
bands from OOF scores, calibrate, fit and persist the final pipeline with a manifest, evaluate
the test set once, and prove reproducibility.

**Independent Test**: `make final` produces `models/final_pipeline.joblib`, `models/manifest.json`
with `test_evaluations: 1`, and test tables; `pytest -q tests/unit/test_threshold.py
tests/unit/test_persist_manifest.py tests/integration/test_reproduce_fixture.py` passes.

- [X] T048 [US1] Implement `src/ssn/modeling/tune.py` and wire `tune --models ...`: `RandomizedSearchCV` over each model's `search_space` with PR-AUC scoring, seeded, on train only; write `reports/tables/tuning_results_<model>.csv` and `reports/tables/tuned_params.json`
  - Type: code
  - Deps: T044
  - Accept: results contain `n_iter` rows per model; best params serialisable
  - Verify: `python -m ssn tune --models logreg random_forest hist_gb && ls reports/tables/tuning_results_*.csv`
- [X] T049 [US4] Implement `src/ssn/fairness/groups.py` (gender group labels from verified encoding; `age_band` from config; refuse gender if `encoding_verified` is false) and `src/ssn/fairness/metrics.py` (selection rate, TPR, FPR, Brier per group; DPD, DIR, EOD, equalized-odds max diff at attribute level with largest group as reference; `n` and `reliable`); write `tests/unit/test_fairness_metrics.py` with hand-computed values and `tests/unit/test_groups_min_size.py`
  - Type: code, tests
  - Deps: T020, T033, T042
  - Accept: metrics match hand calculations; unverified gender raises; small groups flagged
  - Verify: `pytest -q tests/unit/test_fairness_metrics.py tests/unit/test_groups_min_size.py`
- [X] T050 [US1] Wire `select-model`: build `reports/tables/selection_matrix.csv` from tuned CV results (PR-AUC, Recall@K, Precision@K, Brier, ECE), a preliminary OOF fairness summary (max DPD and min DIR across attributes via T049), an explainability feasibility flag, and a maintainability note per model; exclude accuracy; write `reports/tables/selection_decision.json` with the chosen model and a rationale string referencing the matrix; persist each tuned candidate pipeline (refit on full train, `n_jobs=1`) to `models/candidates/<name>.joblib` (Git-ignored) so the single test pass in T054 can load them without refitting
  - Type: code
  - Deps: T048, T049
  - Accept: `accuracy` absent from the matrix; decision JSON present
  - Verify: `python -m ssn select-model && python -c "import pandas as pd;m=pd.read_csv('reports/tables/selection_matrix.csv');assert 'accuracy' not in m.columns;print(m.columns.tolist())"`
- [X] T051 [US1] Implement `src/ssn/modeling/threshold.py` and wire `threshold`: from the selected model's OOF scores compute the capacity threshold (research R-09), band boundaries, F1-optimal and fixed-precision alternatives, Recall@K/Precision@K for the K values derived from `capacity.window_sensitivity_weeks`; write `reports/tables/threshold_and_bands.json` and `reports/tables/oof_recall_precision_at_k.csv`; write `tests/unit/test_threshold.py` (monotone bands, selection rate matches K/N, zero-positive edge case reported)
  - Type: code, tests
  - Deps: T050
  - Accept: JSON has rule, threshold, three bands with supportive names, sensitivity block; tests pass
  - Verify: `python -m ssn threshold && cat reports/tables/threshold_and_bands.json && pytest -q tests/unit/test_threshold.py`
- [X] T052 [US1] Implement `src/ssn/modeling/calibrate.py` and wire `calibrate`: compare uncalibrated versus `CalibratedClassifierCV` (isotonic, sigmoid) within train CV on Brier, ECE, PR-AUC; apply rule from research R-10; write `reports/tables/calibration_comparison.csv` and `reports/figures/oof_calibration.png`; record decision in `reports/tables/calibration_decision.json`
  - Type: code
  - Deps: T050
  - Accept: decision JSON states applied/not and method
  - Verify: `python -m ssn calibrate && cat reports/tables/calibration_decision.json`
- [X] T053 [US1] Implement `src/ssn/modeling/persist.py` and wire `fit-final`: refit selected (optionally calibrated) pipeline on full train with `n_jobs=1`, save `models/final_pipeline.joblib`, write `models/manifest.json` per contracts/artifact-manifest.md (git sha, config hash, pipeline sha256, library versions, data summary, features, estimator, threshold, bands, selection rationale, cv_summary, `test_evaluations: 0`); write `tests/unit/test_persist_manifest.py` (all contract keys present; no row-level data; sha matches file)
  - Type: code, tests, artifacts
  - Deps: T051, T052
  - Accept: manifest validates against the contract key list; sha256 matches
  - Verify: `python -m ssn fit-final && pytest -q tests/unit/test_persist_manifest.py`
- [X] T054 [US1] Wire `evaluate-test`: load the final pipeline plus the dummy baseline and every tuned candidate from `models/candidates/`, read `data/processed/test.parquet` (features and `is_dropout`), and in ONE pass compute all FR-012 to FR-015 metrics for each model at its own OOF-derived threshold and for the K values derived from `capacity.window_sensitivity_weeks`; write `reports/tables/test_metrics_all_models.csv`, `reports/tables/test_metrics.csv` (final model), `test_recall_precision_at_k.csv`, `reports/figures/test_pr_curve.png`, `test_calibration.png`, `test_confusion_matrix.png`; increment `manifest.test_evaluations` once and fill `test_summary`. Selection is already locked by T050; this pass MUST NOT change it. If the final threshold yields zero predicted positives, write the event to `test_metrics.csv` and the manifest (spec edge case)
  - Type: code
  - Deps: T053
  - Accept: `test_metrics_all_models.csv` has a `dummy` row and one row per tuned candidate; manifest `test_evaluations` equals 1 after the pass; a warning is printed if it exceeds 1
  - Verify: `python -m ssn evaluate-test && python -c "import json;m=json.load(open('models/manifest.json'));print(m['test_evaluations'],m['test_summary'])"`
- [X] T055 [P] [US1] Implement `reproduce-check` (compare two run directories of `reports/tables/*.csv` and manifests; write per-metric absolute deltas to `docs/REPRODUCIBILITY.md`) and write `tests/integration/test_reproduce_fixture.py` (two fixture runs with the same seed produce identical CV tables)
  - Type: code, tests, docs
  - Deps: T053
  - Accept: fixture runs identical; command writes a delta table
  - Verify: `pytest -q tests/integration/test_reproduce_fixture.py`
- [X] T056 [US1] Run the final sequence once on real data: `tune`, `select-model`, `threshold`, `calibrate`, `fit-final`, `evaluate-test`; record PV-10 (final K and sensitivity) and PV-11 (all model, threshold, calibration, and test results) as file references in `README.md` and `reports/eda_feature_engineering_report.md` where relevant; commit `models/manifest.json`
  - Type: run, artifacts
  - Deps: T054, T055
  - Accept: `manifest.test_evaluations == 1`; `models/manifest.json` tracked; joblib Git-ignored and README documents `make final` as the regeneration step with the manifest sha256 to compare against
  - Verify: `make final && python -c "import json;assert json.load(open('models/manifest.json'))['test_evaluations']==1" && du -h models/final_pipeline.joblib`
- [X] T057 [US1] Run a second reproduction in a fresh virtual environment (`rm -rf .venv`, reinstall, `make all` into a copy directory) and `reproduce-check`; set the tolerance in `docs/REPRODUCIBILITY.md` to the observed maximum delta plus margin (PV-13) and document any nondeterminism source
  - Type: run, docs
  - Deps: T056
  - Accept: `docs/REPRODUCIBILITY.md` contains the delta table and a stated tolerance; `test_evaluations` remains 1 in the committed manifest (the second run's evaluation happens in the copy directory)
  - Verify: `python -m ssn reproduce-check --runs-a reports --runs-b /tmp/ssn-run2/reports && cat docs/REPRODUCIBILITY.md`

**Checkpoint (MVP for US1)**: Final pipeline, manifest, single test evaluation, and
reproducibility evidence exist.

---

## Phase 7: Explainability, Ethical AI, Fairness Audit, and Model Card (Milestone 7) — US3, US4, US6

**Goal**: SHAP global/local explanations, PDP/ICE, neutral-language mapping, full fairness audit
with mitigation experiment, limitations, and a rendered model card.

**Independent Test**: `make explain && make fairness && python -m ssn model-card` produce
figures, `group_metrics.json` with `n` and `reliable` per group, and `reports/model_card.md`
with no placeholders; `pytest -q tests/unit/test_language_no_sensitive_reasons.py` passes.

- [X] T058 [US3] Implement `src/ssn/explain/shap_explain.py` and wire `explain` (part 1): choose `TreeExplainer` or `LinearExplainer` by estimator type with permutation-importance fallback (recorded in `reports/explainability/method.json`); if the final pipeline is calibrated, explain the fitted base estimator inside the wrapper and record this in `method.json`; compute global importances and local values on test features; map transformed names back to source/engineered names and sum SHAP values across the one-hot columns of each source feature so every factor appears once; write `shap_global_bar.png`, `shap_beeswarm.png`, `shap_values_test.npz` (record_id-indexed), `shap_global_importance.csv`, `shap_local_examples.md` (three anonymised examples)
  - Type: code
  - Deps: T056
  - Accept: outputs written; method JSON states which explainer was used and why
  - Verify: `python -m ssn explain && ls reports/explainability/`
- [X] T059 [US3] Implement `src/ssn/explain/pdp_ice.py` (part 2 of `explain`): select continuous features with at least `explain.pdp_min_distinct_values` distinct values, write `pdp_ice_<feature>.png` for each and `reports/explainability/pdp_ice_selection.csv` listing included and excluded features with reasons
  - Type: code
  - Deps: T058
  - Accept: selection CSV present; every excluded feature has a reason
  - Verify: `cat reports/explainability/pdp_ice_selection.csv`
- [X] T060 [US3] Complete `configs/language.yaml` with an entry for every allow-listed and engineered feature (`label`, `higher_phrase`, `lower_phrase`, `adviser_visible`), marking gender, age, age_band and any audited attribute `adviser_visible: false`; implement `ssn.explain.language.render_local(contributions)` that drops non-visible features and returns supportive phrases; write `tests/unit/test_language_no_sensitive_reasons.py`
  - Type: config, code, tests
  - Deps: T058
  - Accept: `scan-language` reports zero missing feature entries; rendering never includes non-visible features
  - Verify: `pytest -q tests/unit/test_language_no_sensitive_reasons.py && python -m ssn scan-language --paths configs/language.yaml`
- [X] T061 [US4] Implement `src/ssn/fairness/audit.py` and wire `fairness audit`: score test cohort with the saved pipeline, join labels and sensitive columns from `data/evaluation/demo_cohort_labels.parquet`, group via T049, compute per-group and attribute-level metrics at the manifest threshold, group calibration for reliable groups; write `reports/fairness/group_metrics.csv`, `group_metrics.json`, `group_calibration.png`, `selection_rates.png`; refuse to run (exit 2) when gender `encoding_verified` is false
  - Type: code
  - Deps: T049, T056
  - Accept: every group row has `n` and `reliable`; no `record_id` in outputs
  - Verify: `python -m ssn fairness audit && python -c "import json;g=json.load(open('reports/fairness/group_metrics.json'));print([(r['attribute'],r['group'],r['n'],r['reliable']) for r in g['groups']])"`
- [X] T062 [US4] Implement `src/ssn/fairness/mitigate.py` and wire `fairness mitigate`: compare baseline against (a) group-and-label reweighting refit on train and (b) group-specific thresholds equalising selection rate at fixed total K (evaluated on OOF, reported on test once); write `reports/fairness/mitigation_comparison.csv` with fairness and performance deltas and a note that (b) is not deployed
  - Type: code
  - Deps: T061
  - Accept: table has baseline and at least one mitigation row with PR-AUC, Recall@K, DPD, DIR, EOD columns
  - Verify: `python -m ssn fairness mitigate && cat reports/fairness/mitigation_comparison.csv`
- [X] T063 [US3] Run `explain` on real artifacts; verify every figure renders and `shap_local_examples.md` uses neutral phrases via `render_local`
  - Type: run
  - Deps: T059, T060
  - Accept: figures open; `scan-language` passes on `reports/explainability/`
  - Verify: `make explain && python -m ssn scan-language --paths reports/explainability`
- [X] T064 [US4] Run `fairness audit` and `fairness mitigate` on real artifacts; record PV-07 (group sizes, final `min_group_size`) and PV-12 (fairness values) by file reference in `data/README.md` and the report skeleton
  - Type: run
  - Deps: T061, T062
  - Accept: outputs present; any group below `min_group_size` listed in the audit output with a warning
  - Verify: `make fairness && cat reports/fairness/group_metrics.csv`
- [X] T065 [US6] Implement `src/ssn/reporting/model_card.py` and wire `model-card`: render `reports/model_card.md` from `models/manifest.json`, `test_metrics.csv`, `threshold_and_bands.json`, `group_metrics.json`, `calibration_decision.json`, and a hand-written `reports/limitations.md` include; fail if any manifest placeholder remains or if the bare phrase "the model is fair" appears
  - Type: code
  - Deps: T054, T061
  - Accept: model card contains every FR-068 field; command exits non-zero on placeholders
  - Verify: `python -m ssn model-card && grep -nE 'Intended use|Non-use|CC BY 4.0|Threshold|Limitations|Version' reports/model_card.md`
- [X] T066 [US4] Write `reports/limitations.md`: single-institution context, historic inequities, non-causal scores, imbalance, leakage risk and controls, overfitting controls, ambiguous-column decision, unresolved data-quality items, fairness-audit limitations (sample sizes, unverified encodings if any), residual risks; every quantitative statement references a file
  - Type: reports
  - Deps: T064
  - Accept: `scan-language` passes; no unreferenced numbers
  - Verify: `python -m ssn scan-language --paths reports/limitations.md`
- [X] T067 [US6] Run `model-card` on real artifacts and review the rendered card against FR-068
  - Type: run
  - Deps: T065, T066
  - Accept: card renders; `test_evaluations` note present; disclaimer present
  - Verify: `python -m ssn model-card && python -m ssn scan-language --paths reports/model_card.md`
- [X] T068 [P] [US3] Create `notebooks/05_explainability_fairness.ipynb` displaying SHAP figures, PDP/ICE selection, group metrics with warnings, mitigation table, and limitations; execute top-to-bottom
  - Type: notebook
  - Deps: T063, T064
  - Accept: executes; imports from `ssn`; no hand-typed metrics
  - Verify: `jupyter nbconvert --to notebook --execute notebooks/05_explainability_fairness.ipynb --output /tmp/05.ipynb`

**Checkpoint**: Explainability and fairness evidence computed; model card rendered.

---

## Phase 8: Final Report and Two Decks (Milestone 8) — US6

**Goal**: Final report with rubric map and Bias & Fairness Analysis; technical deck (8-12 slides)
and business deck (8-12 slides) built from computed artifacts.

**Independent Test**: `reports/final_report.md` exists with a rubric map linking every
criterion; technical deck slide count is 8-12 by automated check; business deck count recorded.

- [ ] T069 [US6] Implement `src/ssn/reporting/rubric_map.py` and wire `rubric-map`: generate `reports/rubric_map.md` with one row per rubric criterion (from `CAPSTONE_BRIEF.md` Section 5), points, and links to evidencing files or report sections; keep hand-edited link cells across regenerations
  - Type: code, reports
  - Deps: T067
  - Accept: eight rows (seven criteria plus bonus) with points summing to 100; every link resolves
  - Verify: `python -m ssn rubric-map && python - <<'PY'
import re,os
t=open('reports/rubric_map.md').read()
links=re.findall(r'\]\(([^)]+)\)',t); missing=[l for l in links if not l.startswith('#') and not os.path.exists(l.split('#')[0])]
print("links",len(links),"missing",missing); assert not missing
PY`
- [ ] T070 [US6] Write `reports/final_report.md` covering Steps 1-7: problem statement (unit of analysis, prediction point, users, intended use, non-use), dataset and dictionary reference, EDA and feature engineering summary, model comparison and selection rationale, threshold and capacity analysis, test evaluation, explainability, "Bias & Fairness Analysis" (group metrics with n, mitigations, residual risk), limitations (include `reports/limitations.md`), optional steps status, rubric map; every number references a file; every business figure labelled illustrative
  - Type: reports
  - Deps: T069
  - Accept: sections present; `scan-language` passes; no `[PENDING`
  - Verify: `python -m ssn scan-language --paths reports/final_report.md && ! grep -n 'PENDING' reports/final_report.md`
- [ ] T071 [US6] Create `notebooks/90_technical_deck.ipynb` with slide-type cell metadata (8-12 `slide` cells: problem, data, leakage controls, EDA, features, model comparison, threshold and capacity, test results, explainability, fairness, limitations, reproducibility) loading figures and tables from `reports/`; export with nbconvert and check slide count
  - Type: notebook, reports
  - Deps: T070
  - Accept: `reports/decks/technical_deck.slides.html` has 8-12 top-level sections
  - Verify: `jupyter nbconvert notebooks/90_technical_deck.ipynb --to slides --output-dir reports/decks --output technical_deck && python -c "import re;h=open('reports/decks/technical_deck.slides.html').read();n=len(re.findall(r'<section(?![^>]*data-parent)',h));print(n);assert 8<=n<=12"`
- [ ] T072 [US6] Generate `reports/decks/business_deck_outline.md`: per-slide outline (8-12 slides: problem and stakeholders, what the tool does and does not do, illustrative KPI read from `reports/tables/test_recall_precision_at_k.csv` and phrased as the share of eventual dropout cases reached within the illustrative outreach window (per-week capacity times window weeks), risks and safeguards, fairness summary, limitations, rollout strategy, ask) with every figure path and number to paste, all labelled illustrative
  - Type: reports
  - Deps: T070
  - Accept: outline lists 8-12 slides; KPI cites its CSV path
  - Verify: `grep -c '^## Slide' reports/decks/business_deck_outline.md && python -m ssn scan-language --paths reports/decks/business_deck_outline.md`
- [ ] T073 [US6] Author `reports/decks/business_deck.pptx` in PowerPoint or Canva from the outline and exported figures; record the final slide count and export date at the bottom of `business_deck_outline.md`
  - Type: reports
  - Deps: T072
  - Accept: file present; recorded slide count between 8 and 12; no unlabelled ROI figures
  - Verify: `ls -la reports/decks/business_deck.pptx && tail -3 reports/decks/business_deck_outline.md`
- [ ] T074 [US6] Run `scan-language` across `reports/`, `README.md`, `docs/`, `notebooks/` and fix findings
  - Type: run
  - Deps: T071, T073
  - Accept: exit 0
  - Verify: `python -m ssn scan-language --paths reports README.md docs notebooks`
- [ ] T075 [US6] Export `reports/final_report.md` to `reports/final_report.pdf` (pandoc if available, otherwise an editor export) and complete `README.md`: replace every `[PENDING]` with file-referenced values, finish reproduction steps, repository structure, rubric section links, optional-step status
  - Type: docs, reports
  - Deps: T074
  - Accept: PDF exists; README has zero `[PENDING`; README reproduction steps match quickstart.md
  - Verify: `ls reports/final_report.pdf && ! grep -n 'PENDING' README.md`

**Checkpoint**: Report and both decks complete and traceable to computed artifacts.

---

## Phase 9: Dash Application — Student Success Navigator (Milestone 9) — US2, US3, US4, US5, US6

**Goal**: Six-page Dash app that loads the saved pipeline without retraining, serves the
de-identified demo cohort, never shows outcomes or identifiers, gates actions behind human
acknowledgement, and logs actions locally.

**Independent Test**: `pytest -q tests/app` passes; `python -m ssn app` serves six pages;
quickstart.md section 9 walkthrough succeeds.

- [ ] T076 [US2] Implement `src/ssn/app/app.py::create_app(cfg)` and wire `app`: load manifest, verify `model_version == app.expected_model_version` and `pipeline_sha256` matches file (on mismatch serve a single blocking page and no scores), load pipeline with joblib, load `data/demo/demo_cohort.parquet`, call `assert_frame_allowed` on the feature frame, register pages, inject `components/disclaimer.py` and a footer with version metadata into the base layout
  - Type: code
  - Deps: T056, T060
  - Accept: app starts; mismatch config produces the blocking page; no `fit` call anywhere under `src/ssn/app`
  - Verify: `python -m ssn app & sleep 5; curl -s http://127.0.0.1:8050/ | grep -c 'illustrative'; kill %1`
- [ ] T077 [US2] Implement `src/ssn/app/services/scoring.py`: score demo cohort once at startup (`predict_proba`), assign bands from manifest, rank descending with `record_id` ascending tie-break, `top_k(k)` with notice when `k > n`, `score_record(dict)` for hypotheticals; write `tests/app/test_top_k_ranking.py` (exact K rows, tie-break, K > n notice, bands from manifest not recomputed)
  - Type: code, tests
  - Deps: T076
  - Accept: tests pass on a fixture pipeline and manifest
  - Verify: `pytest -q tests/app/test_top_k_ranking.py`
- [ ] T078 [US2] Implement `src/ssn/app/services/actions.py`: create table per contracts/action-log.md if missing, `append_action(...)` INSERT only, `export_csv()`; handle unwritable path by returning a status the UI shows; wire `actions export`; write `tests/app/test_actions_log.py` (append-only: no UPDATE/DELETE strings in module; duplicate record_id creates second row; unwritable path handled; file path matches `.gitignore` rule)
  - Type: code, tests
  - Deps: T076
  - Accept: tests pass; `git check-ignore data/local/actions.sqlite` matches
  - Verify: `pytest -q tests/app/test_actions_log.py && git check-ignore -v data/local/actions.sqlite`
- [ ] T079 [P] [US2] Implement `src/ssn/app/pages/overview.py` (route `/`): purpose, intended use, non-use, illustrative K with label from `capacity.illustrative`, model version and date, cohort size, band legend, disclaimer
  - Type: code
  - Deps: T077
  - Accept: page renders with all listed elements; no outcome or identifier strings
  - Verify: `pytest -q tests/app/test_no_labels_rendered.py -k overview` (after T085)
- [ ] T080 [US2] Implement `src/ssn/app/pages/support_queue.py` (route `/queue`): top-K table (record_id, score 2 dp, band, top-2 neutral factors), K selector limited to the K values derived from `capacity.window_sensitivity_weeks`, K > n notice, "Record support action" opening the acknowledgement modal per contracts/app-pages.md (Save disabled until checkbox; Dismiss/Override always enabled; all three log via `actions.append_action`), toast on success or unwritable notice
  - Type: code
  - Deps: T077, T078
  - Accept: modal flow matches the contract; exactly K rows shown
  - Verify: `pytest -q tests/app -k queue`
- [ ] T081 [US3] Implement `src/ssn/app/services/explanations.py` (load `shap_values_test.npz` or compute with the same explainer type at startup; `render_local` via `ssn.explain.language`) and `src/ssn/app/pages/student_review.py` (route `/review/<record_id>`): score, band, ranked neutral factor phrases with direction, allow-listed feature values with labels, acknowledgement modal, version metadata, disclaimer; sensitive attributes never displayed
  - Type: code
  - Deps: T077, T078, T060
  - Accept: unknown `record_id` shows a not-found message; no non-visible feature appears
  - Verify: `pytest -q tests/app -k review`
- [ ] T082 [US5] Implement `src/ssn/app/pages/new_record.py` (route `/score`): form generated from the allow-list (numeric ranges from `configs/ranges.json`, categorical options from verified encodings in `features.yaml`), server-side validation with field-level messages, result labelled "Hypothetical" with score, band, neutral factors, disclaimer; write `tests/app/test_new_record_validation.py` (missing field, out-of-range, invalid code, valid submission, no second-semester inputs present)
  - Type: code, tests
  - Deps: T077, T081
  - Accept: tests pass; form contains no `second_semester` or `outcome` fields
  - Verify: `pytest -q tests/app/test_new_record_validation.py`
- [ ] T083 [US4] Implement `src/ssn/app/services/equity.py` (read `reports/fairness/group_metrics.json` only; "audit not yet run" state if absent) and `src/ssn/app/pages/equity_dashboard.py` (route `/equity`): attribute toggle, per-group table with `n`, reliable flag and warning, selection rate, TPR, FPR, Brier; attribute-level DPD, DIR, EOD, equalized-odds max diff; calibration plot for reliable groups; residual-risk text from `reports/limitations.md`
  - Type: code
  - Deps: T064, T076
  - Accept: page renders from JSON without computing metrics; small groups show warnings
  - Verify: `pytest -q tests/app -k equity`
- [ ] T084 [P] [US6] Implement `src/ssn/app/pages/model_card.py` (route `/model-card`): render `reports/model_card.md` as markdown
  - Type: code
  - Deps: T067, T076
  - Accept: page shows intended use, non-use, citation, metrics, limitations, version, disclaimer
  - Verify: `pytest -q tests/app -k model_card`
- [ ] T085 [US2] Write `tests/app/test_no_labels_rendered.py` (render every page layout with fixture cohort; assert absence of `Target`, `is_dropout`, outcome-label usages, prohibited terms, and any `adviser_visible: false` feature label), `tests/app/test_forbidden_imports.py` (AST scan of `src/ssn/app/**`: no `.fit(` calls; no import of `ssn.modeling.evaluate`, `ssn.fairness.audit`, `ssn.modeling.tune`; no string containing `data/evaluation` or `data/processed`), `tests/app/test_version_check.py` (mismatched version or sha yields blocking layout and `scoring` never called), and `tests/app/test_queue_to_action_interactions.py` (from the queue layout, the acknowledgement modal's Save is reachable in at most three callback invocations: open record or modal, tick acknowledgement, save; verifies SC-006)
  - Type: tests
  - Deps: T079, T080, T081, T082, T083, T084
  - Accept: all pass; failure messages name the offending page or file
  - Verify: `pytest -q tests/app`
- [ ] T086 [US2] Write `docs/DEPLOYMENT.md` (prerequisites, `make data && make final` or artifact download, `python -m ssn app`, configuration keys, version-mismatch behaviour, action-log location and export, privacy notes) and perform the quickstart.md section 9 manual walkthrough; record the walkthrough date and results at the bottom of `docs/DEPLOYMENT.md`; capture `reports/decks/demo.gif` or a screencast link
  - Type: docs, run
  - Deps: T085
  - Accept: a fresh clone following the guide reaches a running app; walkthrough checklist all ticked, including the count of interactions from opening the Support Queue to a saved acknowledged action (must be three or fewer, recorded in `docs/DEPLOYMENT.md` for SC-006); demo media present
  - Verify: `python -m ssn app & sleep 5; for r in / /queue /score /equity /model-card; do curl -s -o /dev/null -w "$r %{http_code}\n" http://127.0.0.1:8050$r; done; kill %1`

**Checkpoint**: Six pages served from saved artifacts with privacy and acknowledgement
safeguards tested.

---

## Phase 10: Optional MLOps, GenAI, and Demo Work (Milestone 10) — US6

**Goal**: Document optional Step 8 and Step 9 work honestly, or record "not attempted".

**Independent Test**: Each optional item is either present with its verification passing or
listed as not attempted in `README.md` and `reports/final_report.md`.

- [ ] T087 [US6] Write `docs/MLOPS.md`: environment reproducibility (venv, pins, `.python-version`), config-driven runs, manifest-based versioning and rollback procedure (how to restore a previous `models/manifest.json` and joblib and change `app.expected_model_version`), CI description, basic monitoring plan (score distribution drift and group selection-rate drift against baselines read from `reports/fairness/group_metrics.json` and `reports/tables/threshold_and_bands.json`)
  - Type: docs
  - Deps: T057, T064
  - Accept: rollback steps are executable commands; monitoring baselines cite files, not typed numbers
  - Verify: `python -m ssn scan-language --paths docs/MLOPS.md`
- [X] T088 [P] [US6] (pulled forward to 2026-09-10, after Milestone 5, so regressions in Milestones 6-9 are caught on push) Write `.github/workflows/ci.yml`: Python 3.11, install requirements, `ruff check .`, `detect-secrets scan --all-files` (fail on findings), `pytest -q` excluding tests that need real data (marker `needs_data`), on push and pull request
  - Type: config
  - Deps: T085
  - Accept: workflow passes on the remote after push; badge added to README
  - Verify: `gh run list --limit 1` (after push) or `act -l` locally if available
- [ ] T089 [P] [US6] Write `Dockerfile` (python:3.11-slim, copy `src/`, `configs/`, `models/`, `data/demo/`, `reports/fairness/`, `reports/model_card.md`, `reports/explainability/shap_values_test.npz`; run `python -m ssn app --host 0.0.0.0`), `.dockerignore` excluding `data/raw`, `data/processed`, `data/evaluation`, `data/local`, `.env*`, `references/`, and `tests/unit/test_dockerignore.py` asserting those exclusions
  - Type: config, tests
  - Deps: T086
  - Accept: image builds and serves; test passes
  - Verify: `pytest -q tests/unit/test_dockerignore.py && docker build -t ssn . && docker run --rm -d -p 8050:8050 --name ssn ssn && sleep 5 && curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8050/ ; docker rm -f ssn`
- [ ] T090 [P] [US6] Write `docs/GENAI_USE.md`: either "Generative AI was not used" or, for each use, tool, purpose, prompts or examples, human review performed, limitations, and confirmation that no raw student rows were sent to external services; link code or examples in the repo or presentation
  - Type: docs
  - Deps: T075
  - Accept: FR-074 fields present or explicit not-used statement
  - Verify: `python -m ssn scan-language --paths docs/GENAI_USE.md`
- [ ] T091 [US6] Produce demo media: record `reports/decks/demo.gif` or a screencast (link in `docs/DEPLOYMENT.md` and `README.md`) showing the six pages, the acknowledgement modal, and the version-mismatch page; confirm no outcome labels are visible in the recording
  - Type: reports
  - Deps: T086
  - Accept: media present and linked; reviewed for privacy
  - Verify: `ls -la reports/decks/demo.gif || grep -n 'screencast' docs/DEPLOYMENT.md README.md`
- [ ] T092 [US6] Final pre-publication and submission check: run quickstart.md section 11 including the content-level secrets scan, review `git log --oneline` for imperative one-change-per-commit history and squash or reword where needed, update `README.md` and `reports/final_report.md` optional-step status (attempted or not attempted), confirm no private files tracked, rename submission files per course instruction pattern `Your_Name_Assignment name`, and record the checklist completion in `reports/rubric_map.md`
  - Type: run, docs
  - Deps: T087, T088, T089, T090, T091
  - Accept: `clean` output from the tracked-file check; secrets scanner reports no findings; all tests and lint pass; commit history reviewed; submission files named
  - Verify: `git ls-files | grep -Ei 'data/(raw|processed|demo|evaluation|local)/|\.env$|\.sqlite|Pillar5' && echo "STOP" || echo clean; detect-secrets scan --all-files; pytest -q && ruff check .`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Scaffold)**: no dependencies.
- **Phase 2 (Data foundation)**: depends on Phase 1. BLOCKS all stories.
- **Phases 3-6 (US1 model build)**: strictly sequential by milestone: 3 → 4 → 5 → 6.
- **Phase 7**: depends on Phase 6 (T056). Within Phase 7, US3 explainability (T058-T060, T063)
  and US4 fairness (T061, T062, T064) can proceed in parallel; T065-T067 need both.
- **Phase 8**: depends on Phase 7 (T067).
- **Phase 9**: depends on Phase 7 (T056, T060, T064, T067). Can run in parallel with Phase 8.
- **Phase 10**: depends on Phases 8 and 9.

### User Story Dependencies

- **US1** (P1): Phases 3-6. No dependency on other stories. This is the MVP.
- **US2** (P1): Phase 9 core (T076-T080, T085, T086). Depends on US1 artifacts (T056) and the
  language mapping (T060).
- **US3** (P2): T058-T060, T063, T068, T081. Depends on T056.
- **US4** (P2): T049, T061, T062, T064, T066, T083. Depends on T020 (verified gender encoding),
  T033 (age bands), T056.
- **US5** (P3): T082. Depends on T077 and T081.
- **US6** (P3): T065, T067, T069-T075, T084, T087-T092. Depends on US1, US3, US4 outputs.

### Within Each Phase

- Code before its tests only where the test file is named in the same task; otherwise tests
  are separate `[P]` tasks that may be written first and fail until implementation lands.
- `run` tasks come last in a phase and gate the next phase.
- Notebooks and reports follow their `run` task; they display files, never recompute or
  hand-type values.

### Parallel Opportunities

- Phase 1: T003, T004, T005, T007, T008 in parallel after T001/T002.
- Phase 2: T022, T023, T024 in parallel after T019; T025 alongside.
- Phase 3: T030 alongside T031; T034 alongside T035.
- Phase 4: T039 alongside T040 preparation; T041 after T040.
- Phase 5: T045 alongside T046 preparation; T047 after T046.
- Phase 6: T055 alongside T054.
- Phase 7: US3 track (T058-T060) parallel to US4 track (T061-T062); T068 parallel to T065.
- Phase 8 and Phase 9 in parallel once Phase 7 completes.
- Phase 9: T079 and T084 parallel to T080-T083.
- Phase 10: T088, T089, T090 in parallel.

---

## Parallel Example: Phase 7

```bash
# Track A (US3 explainability) and Track B (US4 fairness) after T056:
Task: "T058 [US3] Implement src/ssn/explain/shap_explain.py and wire explain (part 1)"
Task: "T061 [US4] Implement src/ssn/fairness/audit.py and wire fairness audit"
# Then in parallel:
Task: "T059 [US3] Implement src/ssn/explain/pdp_ice.py"
Task: "T060 [US3] Complete configs/language.yaml and render_local"
Task: "T062 [US4] Implement src/ssn/fairness/mitigate.py"
# Join: T063 and T064 (run tasks), then T065-T067 (model card)
```

## Parallel Example: Phase 9

```bash
# After T076-T078:
Task: "T079 [US2] pages/overview.py"
Task: "T080 [US2] pages/support_queue.py"
Task: "T081 [US3] services/explanations.py + pages/student_review.py"
Task: "T083 [US4] services/equity.py + pages/equity_dashboard.py"
Task: "T084 [US6] pages/model_card.py"
# Then T082 (needs T081), then T085 tests, then T086 deployment guide
```

---

## Implementation Strategy

### MVP First (US1: Phases 1-6)

1. Complete Phase 1 (scaffold and guards) and Phase 2 (data foundation, every fact computed).
2. Complete Phases 3-6 in order; stop at each `run` task and inspect the produced tables.
3. **Validate**: `make all` in a fresh environment reproduces `models/manifest.json` within the
   recorded tolerance. This alone evidences rubric Steps 2, 3, 4 and the reproducibility part
   of Step 7.

### Incremental Delivery

1. Add Phase 7 → explainability and fairness evidence (Step 5, 20 points).
2. Add Phase 8 → report and decks (Steps 1, 6, 7 completion).
3. Add Phase 9 → Student Success Navigator (optional Step 8 local deployment, bonus).
4. Add Phase 10 → MLOps/GenAI documentation and demo media (bonus).

### Single-Author Strategy

Work phases sequentially; use the parallel tracks in Phases 7 and 9 to alternate between code
and documentation while long-running commands (tuning, SHAP) execute.

---

## Notes

- `[P]` tasks touch different files and have no dependency on an incomplete task.
- Every `run` task produces the only permitted source for numbers in reports, notebooks,
  README, decks, and the model card.
- Commit after each task or logical group with an imperative message; never commit files under
  `data/raw`, `data/processed`, `data/demo`, `data/evaluation`, `data/local`, or `.env`.
- Stop at any checkpoint to validate the phase independently using quickstart.md.
- If a verification command fails, fix the task before starting the next one; do not carry
  failing gates forward.
