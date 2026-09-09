# Data

## Source and citation

- **Dataset:** Predict Students' Dropout and Academic Success
- **Repository:** UCI Machine Learning Repository
- **URL:** https://archive.ics.uci.edu/dataset/697/predict+students+dropout+and+academic+success
- **DOI:** 10.24432/C5MC89
- **Creators:** Valentim Realinho, Mónica Vieira Martins, Jorge Machado, Luís Baptista (Instituto
  Politécnico de Portalegre)
- **Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0),
  https://creativecommons.org/licenses/by/4.0/
- **Recommended citation:** Realinho, V., Vieira Martins, M., Machado, J., & Baptista, L. (2021).
  Predict Students' Dropout and Academic Success [Dataset]. UCI Machine Learning Repository.
  https://doi.org/10.24432/C5MC89
- **Licence terms verified:** yes, 2026-09-10 (CC BY 4.0 deed read; attribution requirement satisfied by this
  file, `reports/data_overview.md`, the final report, and both decks)
- **Introductory paper (UCI "citation" field):** Martins, M.V., Tolledo, D., Machado, J., Baptista, L.M.T.,
  Realinho, V. (2021). Early prediction of student's performance in higher education: a case study.
  *Trends and Applications in Information Systems and Technologies*, AISC, Springer. DOI 10.1007/978-3-030-72657-7_16
- **Variable documentation:** UCI variables table via https://archive.ics.uci.edu/api/dataset?id=697 (retrieved 2026-09-10)

## Access and licence verification checklist (completed 2026-09-10)

- [x] Dataset page and licence (CC BY 4.0) read at the URL above
- [x] Attribution recorded here and in `reports/data_overview.md`; to be repeated in report and decks
- [x] Raw file Git-ignored (`data/raw/*`), only `.gitkeep` tracked
- [x] SHA-256 of `data.csv` recorded in `configs/base.yaml` and below; `data download` refuses a mismatch
- [x] Source column spelling preserved ("Nacionality"); header whitespace/BOM normalised on load only
- [x] Variable encodings copied from the UCI variables table; every observed code checked against them
- [ ] Source article (Realinho et al., 2022, *Data* 7(11):146, DOI 10.3390/data7110146) read manually for
      the recording time of Debtor / Tuition fees up to date / Scholarship holder — see "Open verification items"

## Provenance statement

The data are de-identified historical records from a single higher-education institution. They
MUST NOT be represented as data from a Philippine university or as representative of universities
in general. Historic outcomes may encode institutional inequities; predicted risk is not causal.

## Acquisition

Raw data are **not committed**. `data/raw/` is Git-ignored except for its `.gitkeep`.

- Download command: `python -m ssn data download` (fetches the UCI zip, extracts `data.csv`, verifies the hash).
  Manual alternative: download the zip from the UCI page and run
  `python -m ssn data download --from-local /path/to/data.csv`.
- Expected file: `data/raw/data.csv` (semicolon-delimited, UTF-8 with BOM, 4425 lines incl. header)
- SHA-256 of `data.csv`: `3ef126de5cefff26eb11fbb4237f1a1401cb64b488e2f1d598c23cedeb4c45ae`
  (zip archive sha256 `e90e55fd65ec462ae283ebeb2cca409319e3460ed898d8754f62fb35cc83a65d`, retrieved 2026-09-10)
- If the file is absent, every `ssn data ...` command fails with an explicit message pointing here. No data
  is ever synthesised in its place.

## Directory layout

| Directory | Contents | Audience | Tracked |
|-----------|----------|----------|---------|
| `raw/` | Original UCI CSV | pipeline | no |
| `interim/` | Intermediate cleaning outputs | pipeline | no |
| `processed/` | `train.parquet`, `test.parquet`, OOF predictions | pipeline | no |
| `demo/` | De-identified demo cohort: synthetic `record_id` plus allow-listed features only. No outcomes, no sensitive columns. | app (adviser-facing) | no |
| `evaluation/` | Evaluator-only labels and sensitive columns for the demo cohort | evaluation and fairness audit only; never read by the app | no |
| `local/` | SQLite action log and exports | app runtime | no |

## Profiling results (computed 2026-09-10 by `python -m ssn data profile`)

Source files: `reports/tables/profile_*.csv`, `reports/tables/validate_report.json`,
`reports/data_overview.md`. Numbers below are copied from those files.

- Rows × columns: **4424 × 37** (matches UCI: 4424 instances, 36 features + Target)
- Missing cells: **0** (UCI declares no missing values; confirmed)
- Exact duplicate rows: **0**; duplicate feature rows ignoring Target: **0**
- Values violating documented codes/ranges: **0 rule hits** (`profile_invalid_values.csv`);
  all observed categorical codes appear in the UCI documentation
- Age at enrollment: min 17, median 20, max 70, mean 23.27
  (input to PV-06 age-band decision in Milestone 3)
- First-semester zero denominators (PV-08 input): 180 records with 0 units enrolled; 718 with grade 0 and 0 approved;
  0 records with approved > enrolled

### Target distribution (observed)

| Target | Count | Share | is_dropout |
|--------|-------|-------|------------|
| Graduate | 2209 | 0.4993 | 0 |
| Dropout | 1421 | 0.3212 | 1 |
| Enrolled | 794 | 0.1795 | 0 |

Derived `is_dropout` positive rate: **0.3212** (1421 of 4424).

## Column classification (configs/features.yaml, generated 2026-09-10)

| Class | Count | Columns |
|-------|-------|---------|
| Allowed model inputs (enrollment + first semester, role feature) | 21 | 15 enrollment-time + 6 first-semester |
| Sensitive, audit-only (never model inputs) | 6 | Gender, Age at enrollment, Nacionality, International, Marital status, Educational special needs |
| Ambiguous timing, excluded by default | 3 | Debtor, Tuition fees up to date, Scholarship holder |
| Second semester, prohibited | 6 | Curricular units 2nd sem (6 columns) |
| Target | 1 | Target |
| Unclassified | 0 | — |

Encodings: all 22 coded columns verified against the UCI variables table (every observed code documented).
Gender: 1 = male, 0 = female. Full dictionary with codes and observed counts: `data/data_dictionary.md`.

## Open verification items

- **Recording time of Debtor, Tuition fees up to date, Scholarship holder.** Not stated in the UCI variables
  table. The source article (MDPI, DOI 10.3390/data7110146) returned HTTP 403 to programmatic access on
  2026-09-10 and has not yet been read manually. Until confirmed, these columns stay `ambiguous` and excluded
  from the deployed model; Milestone 5 reports an ablation with them included for transparency.
- **Documentation typo.** UCI describes "Curricular units 2nd sem (without evaluations)" as "1st semester";
  treated as a typo, column classified second semester by name.
- **Macroeconomic year alignment.** UCI groups Unemployment rate, Inflation rate, GDP with "information known at
  the time of student enrollment"; the exact reference year per record is not documented.
