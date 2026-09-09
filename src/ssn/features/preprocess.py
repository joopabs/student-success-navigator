"""ColumnTransformer builder (T029). Builds; never fits here.

Fitting happens only inside cross-validation folds or on the training split (Milestone 4+).
"""

from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ssn.features.allowlist import Allowlist
from ssn.features.engineering import ENGINEERED_NAMES, Sem1FeatureEngineer


def feature_groups(allow: Allowlist) -> dict[str, list[str]]:
    numeric = [c for c in allow.allowed_source if allow.columns[c]["dtype"] == "numeric"]
    binary = [c for c in allow.allowed_source if allow.columns[c]["dtype"] == "binary"]
    categorical = [c for c in allow.allowed_source if allow.columns[c]["dtype"] == "categorical"]
    return {
        "numeric": sorted(numeric) + ENGINEERED_NAMES,
        "binary": sorted(binary),
        "categorical": sorted(categorical),
    }


def build_preprocessor(allow: Allowlist, *, scale_numeric: bool = True) -> Pipeline:
    """engineer -> (impute+scale numeric | passthrough binary | impute+one-hot categorical)."""
    groups = feature_groups(allow)
    numeric_steps = [("impute", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scale", StandardScaler()))
    ct = ColumnTransformer(
        transformers=[
            ("num", Pipeline(numeric_steps), groups["numeric"]),
            ("bin", SimpleImputer(strategy="most_frequent"), groups["binary"]),
            (
                "cat",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                groups["categorical"],
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )
    return Pipeline([("engineer", Sem1FeatureEngineer()), ("columns", ct)])


def project_for_model(df: pd.DataFrame, allow: Allowlist) -> pd.DataFrame:
    """Allow-listed source columns only; engineered features are added inside the pipeline."""
    X = allow.project_features(df)
    X = X[[c for c in X.columns if c in allow.allowed_source]]
    allow.assert_frame_allowed(X)
    return X
