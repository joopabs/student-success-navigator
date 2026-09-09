"""Leakage-safe, stateless first-semester feature engineering (T028).

All features use enrollment-time or first-semester inputs only. The transformer has no fitted
state (fit is a no-op), so it can run inside a scikit-learn Pipeline without ever seeing labels or
test rows during fitting. Zero denominators yield NaN, counted for the report; imputation happens
later inside the CV pipeline, never here.

`age_band` is an AUDIT-ONLY helper: it derives from a sensitive column and is never a model input.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

SEM1 = {
    "credited": "Curricular units 1st sem (credited)",
    "enrolled": "Curricular units 1st sem (enrolled)",
    "evaluations": "Curricular units 1st sem (evaluations)",
    "approved": "Curricular units 1st sem (approved)",
    "grade": "Curricular units 1st sem (grade)",
    "without_eval": "Curricular units 1st sem (without evaluations)",
}
ADMISSION_GRADE = "Admission grade"
PREV_GRADE = "Previous qualification (grade)"

# name -> (inputs, academic rationale)
FEATURE_SPECS: dict[str, tuple[list[str], str]] = {
    "sem1_approval_rate": (
        [SEM1["approved"], SEM1["enrolled"]],
        "Share of enrolled first-semester units passed: the most direct early signal of "
        "academic progress.",
    ),
    "sem1_evaluation_participation_rate": (
        [SEM1["evaluations"], SEM1["enrolled"]],
        "Evaluations sat per enrolled unit: engagement with assessment, distinct from passing.",
    ),
    "sem1_non_evaluation_rate": (
        [SEM1["without_eval"], SEM1["enrolled"]],
        "Share of enrolled units with no evaluation at all: a disengagement or withdrawal signal.",
    ),
    "grade_diff_vs_admission": (
        [SEM1["grade"], ADMISSION_GRADE],
        "First-semester grade (0-20 scale, rescaled to 0-200) minus admission grade (0-200): "
        "change in performance relative to entry level.",
    ),
    "sem1_credited_share": (
        [SEM1["credited"], SEM1["enrolled"]],
        "Share of enrolled units credited from prior study: workload actually taken is lower.",
    ),
    "sem1_load": (
        [SEM1["enrolled"]],
        "Number of first-semester units enrolled: workload proxy (kept explicit for "
        "interpretability).",
    ),
    "sem1_any_approved": (
        [SEM1["approved"]],
        "Whether at least one unit was passed: separates zero-progress students from the rest.",
    ),
}

ENGINEERED_NAMES = list(FEATURE_SPECS)


def _safe_rate(num: pd.Series, den: pd.Series) -> pd.Series:
    den = den.astype(float)
    out = num.astype(float) / den.where(den != 0, np.nan)
    return out


def engineer(df: pd.DataFrame) -> pd.DataFrame:
    """Return a frame of engineered features aligned to df.index (no mutation of df)."""
    s1 = {k: df[v] for k, v in SEM1.items() if v in df.columns}
    out = pd.DataFrame(index=df.index)
    out["sem1_approval_rate"] = _safe_rate(s1["approved"], s1["enrolled"])
    out["sem1_evaluation_participation_rate"] = _safe_rate(s1["evaluations"], s1["enrolled"])
    out["sem1_non_evaluation_rate"] = _safe_rate(s1["without_eval"], s1["enrolled"])
    # grade scales: 1st-sem grade is 0-20, admission grade is 0-200 (UCI docs) -> rescale x10
    out["grade_diff_vs_admission"] = s1["grade"].astype(float) * 10.0 - df[ADMISSION_GRADE].astype(
        float
    )
    out["sem1_credited_share"] = _safe_rate(s1["credited"], s1["enrolled"])
    out["sem1_load"] = s1["enrolled"].astype(float)
    out["sem1_any_approved"] = (s1["approved"] > 0).astype(int)
    return out


def zero_denominator_counts(df: pd.DataFrame) -> pd.DataFrame:
    den = df[SEM1["enrolled"]]
    n_zero = int((den == 0).sum())
    return pd.DataFrame(
        [
            {
                "feature": name,
                "denominator": SEM1["enrolled"],
                "n_zero_denominator": n_zero,
                "handling": "NaN; imputed inside the CV pipeline (never fitted here)",
            }
            for name in (
                "sem1_approval_rate",
                "sem1_evaluation_participation_rate",
                "sem1_non_evaluation_rate",
                "sem1_credited_share",
            )
        ]
    )


def age_band(age: pd.Series, bands: list[dict]) -> pd.Series:
    """Map age to configured bands [{name, lower, upper}] (inclusive bounds). Empty bands -> NA."""
    if not bands:
        return pd.Series(pd.NA, index=age.index, dtype="object")
    out = pd.Series(pd.NA, index=age.index, dtype="object")
    for b in bands:
        mask = (age >= b["lower"]) & (age <= b["upper"])
        out[mask] = b["name"]
    return out


@dataclass
class Sem1FeatureEngineer(BaseEstimator, TransformerMixin):
    """Stateless transformer: appends engineered features to the input frame."""

    drop_inputs: bool = False
    feature_names_in_: list[str] = field(default_factory=list, repr=False)

    def get_input_columns(self) -> list[str]:
        cols: list[str] = []
        for inputs, _ in FEATURE_SPECS.values():
            cols.extend(c for c in inputs if c not in cols)
        return cols

    def fit(self, X: pd.DataFrame, y=None):  # noqa: D401 - sklearn API
        """No-op: nothing is learned from the data."""
        self.feature_names_in_ = list(X.columns)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        eng = engineer(X)
        for c in eng.columns:
            X[c] = eng[c]
        if self.drop_inputs:
            X = X.drop(columns=[c for c in self.get_input_columns() if c in X.columns])
        return X

    def get_feature_names_out(self, input_features=None):
        base = list(input_features) if input_features is not None else list(self.feature_names_in_)
        if self.drop_inputs:
            base = [c for c in base if c not in self.get_input_columns()]
        return np.asarray(base + ENGINEERED_NAMES, dtype=object)
