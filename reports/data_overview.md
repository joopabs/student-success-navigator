# Data Overview

**Generated:** 2026-09-12 16:58 UTC by `python -m ssn data profile`. Every number below is computed from
`data/raw/data.csv` (sha256 `3ef126de5cefff26eb11fbb4237f1a1401cb64b488e2f1d598c23cedeb4c45ae`). Hand-written commentary lives in the notes block.

## 1. Source and citation

- **Dataset:** Predict Students' Dropout and Academic Success (UCI ML Repository id 697)
- **URL:** https://archive.ics.uci.edu/dataset/697/predict+students+dropout+and+academic+success
- **DOI:** 10.24432/C5MC89 · **Licence:** CC BY 4.0
- **Creators:** Valentim Realinho, Mónica Vieira Martins, Jorge Machado, Luís Baptista
  (Instituto Politécnico de Portalegre)
- **Citation (UCI recommended):** Realinho, V., Vieira Martins, M., Machado, J., & Baptista, L. (2021).
  Predict Students' Dropout and Academic Success [Dataset]. UCI Machine Learning Repository.
  https://doi.org/10.24432/C5MC89
- **Introductory paper (UCI "citation" field):** Martins, M.V., Tolledo, D., Machado, J., Baptista, L.M.T.,
  Realinho, V. (2021). Early prediction of student's performance in higher education: a case study.
  *Trends and Applications in Information Systems and Technologies*, AISC, Springer.
  DOI 10.1007/978-3-030-72657-7_16
- **Funding (UCI):** SATDAP – Capacitação da Administração Pública, grant POCI-05-5762-FSE-000191, Portugal.

## 2. Access and licence verification checklist

See `data/README.md` for the dated checklist. Items: licence text read; attribution present in
README, report, and decks; raw file Git-ignored; checksum recorded; source spelling preserved.

## 3. Unit of analysis and target

- **Unit of analysis:** one student enrollment record ("Each instance is a student").
- **Source target:** `Target`, three classes "at the end of the normal duration
  of the course" (UCI). **Deployed target:** `is_dropout` = 1 where Target = Dropout,
  else 0 (PROJECT_DECISIONS).

### Target distribution (observed)

| label | count | share | is_dropout |
|---|---|---|---|
| Graduate | 2209 | 0.4993 | 0 |
| Dropout | 1421 | 0.3212 | 1 |
| Enrolled | 794 | 0.1795 | 0 |

Derived `is_dropout` positive rate: **0.3212**.

## 4. Shape and column classification (observed)

- Rows: **4424** · Columns: **37** (36 features + Target per UCI; verified against the file)
- Availability classes: {'ambiguous': 3, 'enrollment': 21, 'first_semester': 6, 'outcome': 1, 'second_semester': 6}
- Roles: allowed model inputs = 21, sensitive (audit-only) = 6,
  ambiguous (excluded by default) = 3, second semester (prohibited) = 6,
  target = 1, unclassified = 0
- Declared types: {'binary': 8, 'categorical': 10, 'numeric': 19}

## 5. Missingness

Total missing cells across all columns: **0** (UCI declares "has_missing_values: no").

_No missing values observed in any column._

## 6. Duplicates

| rule | count |
|---|---|
| exact duplicate rows (all columns) | 0 |
| duplicate feature rows ignoring Target | 0 |
| duplicate feature rows with conflicting Target | 0 |

## 7. Invalid values against documentation

Rules: non-numeric/missing, code not in UCI documentation, outside documented range, negative counts.

_No values violate the documented codes or ranges._

Columns with documented codes but **unverified** encoding: none.
Columns whose observed codes fall **outside** documentation: none.

## 8. Outlier candidates (IQR fences, numeric columns)

Counts only; treatment decisions belong to Milestone 3 and must be justified there.

| column | q1 | q3 | iqr_low_fence | iqr_high_fence | n_below | n_above | n_zero |
|---|---|---|---|---|---|---|---|
| Application order | 1 | 2 | -0.5 | 3.5 | 0 | 541 | 1 |
| Previous qualification (grade) | 125 | 140 | 102.5 | 162.5 | 93 | 86 | 0 |
| Admission grade | 117.9 | 134.8 | 92.55 | 160.2 | 0 | 86 | 0 |
| Age at enrollment | 19 | 25 | 10 | 34 | 0 | 441 | 0 |
| Curricular units 1st sem (credited) | 0 | 0 | 0 | 0 | 0 | 577 | 3847 |
| Curricular units 1st sem (enrolled) | 5 | 7 | 2 | 10 | 187 | 237 | 180 |
| Curricular units 1st sem (evaluations) | 6 | 10 | 0 | 16 | 0 | 158 | 349 |
| Curricular units 1st sem (approved) | 3 | 6 | -1.5 | 10.5 | 0 | 180 | 718 |
| Curricular units 1st sem (grade) | 11 | 13.4 | 7.4 | 17 | 718 | 8 | 718 |
| Curricular units 1st sem (without evaluations) | 0 | 0 | 0 | 0 | 0 | 294 | 4130 |
| Curricular units 2nd sem (credited) | 0 | 0 | 0 | 0 | 0 | 530 | 3894 |
| Curricular units 2nd sem (enrolled) | 5 | 7 | 2 | 10 | 183 | 186 | 180 |
| Curricular units 2nd sem (evaluations) | 6 | 10 | 0 | 16 | 0 | 109 | 401 |
| Curricular units 2nd sem (approved) | 2 | 6 | -4 | 12 | 0 | 44 | 870 |
| Curricular units 2nd sem (grade) | 10.75 | 13.33 | 6.875 | 17.21 | 870 | 7 | 870 |
| Curricular units 2nd sem (without evaluations) | 0 | 0 | 0 | 0 | 0 | 282 | 4142 |
| Unemployment rate | 9.4 | 13.9 | 2.65 | 20.65 | 0 | 0 | 0 |
| Inflation rate | 0.3 | 2.6 | -3.15 | 6.05 | 0 | 0 | 0 |
| GDP | -1.7 | 1.79 | -6.935 | 7.025 | 0 | 0 | 0 |

## 9. Dataset limitations (documented, not inferred from results)

- Single institution in Portugal; not representative of Philippine or other institutions.
- Historic outcomes may encode institutional inequities; predicted risk is not causal.
- "Enrolled" students had not yet graduated or left at the observation horizon; the binary target
  treats them as non-dropout by project decision.
- Financial-status fields (Debtor, Tuition fees up to date, Scholarship holder) have no documented
  recording time and are classified `ambiguous` and excluded by default (leakage guard).
- Macroeconomic indicators are annual national figures, not student-level attributes.
- UCI states preprocessing removed anomalies, outliers, and missing values before publication;
  the cleaning history is therefore not fully observable.
- The documentation entry for "Curricular units 2nd sem (without evaluations)" says "1st semester";
  treated as a documentation typo.

<!-- BEGIN NOTES -->
_Add hand-written notes here; this block survives regeneration._
<!-- END NOTES -->
