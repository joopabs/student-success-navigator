"""Documented cleaning of the raw dataset (T026).

Every treatment is row-wise and deterministic; nothing here is fitted (no imputation statistics,
no scaling). Before/after counts are written so the EDA report can cite them. Rows are only
removed for hard violations of the documented schema; outliers are flagged, never removed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from ssn.config import Config
from ssn.features.allowlist import Allowlist

SEM1_ENROLLED = "Curricular units 1st sem (enrolled)"
SEM1_APPROVED = "Curricular units 1st sem (approved)"
SEM1_GRADE = "Curricular units 1st sem (grade)"


@dataclass
class CleanResult:
    frame: pd.DataFrame
    log: list[dict] = field(default_factory=list)

    def table(self) -> pd.DataFrame:
        return pd.DataFrame(
            self.log, columns=["issue", "column", "count_before", "count_after", "treatment"]
        )


def _log(
    res: CleanResult, issue: str, column: str, before: int, after: int, treatment: str
) -> None:
    res.log.append(
        {
            "issue": issue,
            "column": column,
            "count_before": int(before),
            "count_after": int(after),
            "treatment": treatment,
        }
    )


def clean(df: pd.DataFrame, cfg: Config, allow: Allowlist) -> CleanResult:
    res = CleanResult(frame=df.copy())
    f = res.frame
    target = cfg.get("data.target_column")
    expected_labels = set(cfg.get("data.target_expected_labels"))

    # 1. Header whitespace already normalised by schema.load_raw; record for transparency.
    _log(res, "header whitespace/BOM", "<all>", 0, 0, "stripped on load (schema.load_raw)")

    # 2. Exact duplicate rows -> drop (keep first).
    n_dup = int(f.duplicated().sum())
    f = f.drop_duplicates(keep="first")
    _log(res, "exact duplicate rows", "<all>", n_dup, int(f.duplicated().sum()), "drop, keep first")

    # 3. Target label outside documentation -> drop row.
    bad_t = ~f[target].isin(expected_labels)
    _log(res, "undocumented Target label", target, int(bad_t.sum()), 0, "drop row")
    f = f.loc[~bad_t]

    # 4. Numeric coercion for every non-target column; non-numeric -> NaN, then row dropped
    #    (UCI documents no missing values, so none are expected).
    for col in allow.columns:
        if col == target or col not in f.columns:
            continue
        coerced = pd.to_numeric(f[col], errors="coerce")
        n_bad = int(coerced.isna().sum() - f[col].isna().sum())
        if n_bad:
            _log(res, "non-numeric value", col, n_bad, 0, "coerce to NaN then drop row")
        f[col] = coerced
    n_na_rows = int(f.drop(columns=[target]).isna().any(axis=1).sum())
    _log(
        res,
        "rows with any missing value",
        "<all>",
        n_na_rows,
        0,
        "drop row (UCI: no missing values)",
    )
    f = f.dropna()

    # 5. Codes outside documentation -> drop row (documented codes are exhaustive per UCI table).
    for col, meta in allow.columns.items():
        if not meta.get("codes") or col not in f.columns:
            continue
        documented = {int(k) for k in meta["codes"]}
        bad = ~f[col].astype(int).isin(documented)
        if bad.any():
            _log(res, "code not in UCI documentation", col, int(bad.sum()), 0, "drop row")
            f = f.loc[~bad]

    # 6. Values outside documented ranges -> drop row.
    for col, meta in allow.columns.items():
        if not meta.get("range") or col not in f.columns:
            continue
        lo, hi = meta["range"]
        bad = (f[col] < lo) | (f[col] > hi)
        if bad.any():
            _log(res, f"outside documented range [{lo}, {hi}]", col, int(bad.sum()), 0, "drop row")
            f = f.loc[~bad]

    # 7. Integrity checks specific to first-semester counts (flag only; documented as data facts).
    if {SEM1_APPROVED, SEM1_ENROLLED}.issubset(f.columns):
        n_more_approved = int((f[SEM1_APPROVED] > f[SEM1_ENROLLED]).sum())
        _log(
            res,
            "approved > enrolled (1st sem)",
            SEM1_APPROVED,
            n_more_approved,
            n_more_approved,
            "flag only; none expected",
        )
        n_zero_enrolled = int((f[SEM1_ENROLLED] == 0).sum())
        _log(
            res,
            "zero units enrolled (1st sem)",
            SEM1_ENROLLED,
            n_zero_enrolled,
            n_zero_enrolled,
            "keep; rate features become NaN for these rows (imputed inside CV later)",
        )
    if SEM1_GRADE in f.columns and SEM1_APPROVED in f.columns:
        n_zero_grade = int((f[SEM1_GRADE] == 0).sum())
        _log(
            res,
            "grade == 0 (1st sem)",
            SEM1_GRADE,
            n_zero_grade,
            n_zero_grade,
            "keep; coincides with zero approvals, a real academic state not an error",
        )

    # 8. Outliers: IQR flags are reported in profile_outliers.csv; nothing removed.
    _log(
        res,
        "IQR outlier candidates",
        "<numeric>",
        -1,
        -1,
        "keep all; see reports/tables/profile_outliers.csv; tree models are robust, "
        "logistic regression is scaled inside the CV pipeline",
    )

    res.frame = f.reset_index(drop=True)
    _log(res, "rows", "<all>", len(df), len(res.frame), "net effect of all treatments")
    return res
