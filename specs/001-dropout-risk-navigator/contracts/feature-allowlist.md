# Contract: Feature Allow-List (`configs/features.yaml`)

Owned by M2. Enforced by `ssn.features.allowlist` and `tests/unit/test_allowlist.py`.

## Structure

```yaml
columns:
  - name: "<exact source column name>"
    availability: enrollment | first_semester | second_semester | outcome | ambiguous
    role: feature | sensitive | target | id | excluded
    dtype: numeric | categorical | binary
    adviser_visible: true | false
    encoding_source: "UCI variables table" | "Realinho et al. 2022" | "unverified"
    encoding_verified: true | false
    note: "<why this availability class>"
engineered:
  - name: sem1_approval_rate
    inputs: ["<1st-sem approved col>", "<1st-sem enrolled col>"]
    adviser_visible: true
```

## Rules enforced in code

1. Every column present in `data/raw/data.csv` MUST appear exactly once under `columns`.
   Unknown or missing columns fail `data validate` and the unit test.
2. Allow-list = columns with `role: feature` and `availability in {enrollment, first_semester}`,
   plus `engineered` entries whose every input is itself allow-listed.
3. Columns with `availability in {second_semester, outcome, ambiguous}` are prohibited for the
   deployed model. `ambiguous` columns may be promoted only by changing `availability` with a
   `note` citing the documentation that confirms first-semester availability (research R-05).
4. `role: sensitive` columns are never model features and never `adviser_visible: true`. They are
   passed through to the evaluation cohort for aggregate auditing only.
5. `role: target` is exactly one column (`Target`); `is_dropout` is derived, not listed.
6. `ssn.features.allowlist.project_features(df)` returns only allow-listed columns, and
   `assert_frame_allowed(X)` raises `LeakageError` naming any column in `X` that is not
   allow-listed. Every training and inference path, including the app's scoring service, MUST
   call `project_features` and then `assert_frame_allowed` on the result before fitting or
   predicting. Full frames carrying `is_dropout` or sensitive columns are permitted upstream of
   projection only.

## Expected availability families (to confirm in PV-03)

Public documentation for this dataset describes column families of these kinds. Their exact
names are recorded in M2, not here.

| Family | Proposed availability | Confirmation needed |
|--------|-----------------------|---------------------|
| Demographics and application details (marital status, application mode/order, course, attendance regime, nationality, prior qualification and grade, parents' qualification/occupation, admission grade, displaced, special needs, international, gender, age at enrollment) | `enrollment` | Confirm each is known at enrollment |
| Financial/administrative status (tuition fees up to date, debtor, scholarship holder) | `ambiguous` (excluded by default) | Timing of status snapshot undocumented; ablation in M3 |
| Macro-economic indicators (unemployment, inflation, GDP) | `enrollment` | Confirm they refer to enrollment year |
| Curricular units 1st semester (credited, enrolled, evaluations, approved, grade, without evaluations) | `first_semester` | Confirm naming |
| Curricular units 2nd semester (same six) | `second_semester` (prohibited) | Confirm naming |
| `Target` | `outcome` / role target | PV-02 |

Sensitive attributes for auditing: gender (role `sensitive`, after encoding verified) and
derived `age_band` (from age at enrollment; the raw age column remains a feature candidate, the
band is audit-only). Any additional sensitive field requires a documented justification in
`PROJECT_DECISIONS.md` before its role is set to `sensitive`.
