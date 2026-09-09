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
- **Licence terms verified:** `[PENDING: T025, with access date]`

## Provenance statement

The data are de-identified historical records from a single higher-education institution. They
MUST NOT be represented as data from a Philippine university or as representative of universities
in general. Historic outcomes may encode institutional inequities; predicted risk is not causal.

## Acquisition

Raw data are **not committed**. `data/raw/` is Git-ignored except for its `.gitkeep`.

- Download command: `[PENDING: python -m ssn data download, Milestone 2 T015]`
- Expected file: `data/raw/data.csv`
- SHA-256 of the downloaded file: `[PENDING: recorded in configs/base.yaml data.expected_sha256]`

## Directory layout

| Directory | Contents | Audience | Tracked |
|-----------|----------|----------|---------|
| `raw/` | Original UCI CSV | pipeline | no |
| `interim/` | Intermediate cleaning outputs | pipeline | no |
| `processed/` | `train.parquet`, `test.parquet`, OOF predictions | pipeline | no |
| `demo/` | De-identified demo cohort: synthetic `record_id` plus allow-listed features only. No outcomes, no sensitive columns. | app (adviser-facing) | no |
| `evaluation/` | Evaluator-only labels and sensitive columns for the demo cohort | evaluation and fairness audit only; never read by the app | no |
| `local/` | SQLite action log and exports | app runtime | no |

## Profiling results

`[PENDING: Milestone 2 T018. Row and column counts, Target values and derived is_dropout balance,
missingness, duplicates, and ranges are recorded here only after being computed by
`python -m ssn data profile` and written to reports/tables/profile_*.csv.]`

## Column classification

`[PENDING: Milestone 2 T019/T020. Every column is classified by availability time in
configs/features.yaml; the data dictionary with verified encodings is data/data_dictionary.md.]`

## Open verification items

`[PENDING: populated if any encoding cannot be verified against the UCI variables table or the
source article (Realinho et al., 2022, Data 7(11):146).]`
