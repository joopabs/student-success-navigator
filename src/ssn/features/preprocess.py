"""ColumnTransformer builder (T029). Builds; never fits here.

Fitting happens only inside cross-validation folds or on the training split (Milestone 4+).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
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


class Preprocessor(BaseEstimator, TransformerMixin):
    """Single-step wrapper around `engineer -> ColumnTransformer`.

    A single transformer (not a nested Pipeline) so it can sit inside an imbalanced-learn Pipeline,
    which rejects Pipeline objects as intermediate steps. `named_steps` is exposed for callers that
    inspect the inner ColumnTransformer (e.g. `named_steps["columns"].get_feature_names_out()`).
    """

    def __init__(self, allow: Allowlist, scale_numeric: bool = True):
        self.allow = allow
        self.scale_numeric = scale_numeric

    def _build(self) -> Pipeline:
        return _build_pipeline(self.allow, scale_numeric=self.scale_numeric)

    def fit(self, X: pd.DataFrame, y=None):
        self.pipeline_ = self._build().fit(X, y)
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        return self.pipeline_.transform(X)

    def get_feature_names_out(self, input_features=None):
        return self.pipeline_.named_steps["columns"].get_feature_names_out()

    @property
    def named_steps(self):
        return self.pipeline_.named_steps

    def __sklearn_is_fitted__(self) -> bool:
        return hasattr(self, "pipeline_")


def build_preprocessor(allow: Allowlist, *, scale_numeric: bool = True) -> Preprocessor:
    """engineer -> (impute+scale numeric | passthrough binary | impute+one-hot categorical)."""
    return Preprocessor(allow, scale_numeric=scale_numeric)


def _build_pipeline(allow: Allowlist, *, scale_numeric: bool = True) -> Pipeline:
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
