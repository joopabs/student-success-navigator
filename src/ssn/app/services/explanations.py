"""Local explanations for adviser pages.

Demo-cohort explanations are LOADED from the precomputed SHAP matrix written by `ssn explain`
(reports/explainability/shap_values_test.npz), aligned by synthetic record_id. Hypothetical records
are explained on demand with the same explainer path. Rendering goes through
`ssn.explain.language.render_local`, which drops every sensitive attribute.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ssn.explain.language import LanguageRules, render_local
from ssn.features.engineering import engineer


class PrecomputedShap:
    def __init__(
        self, values: np.ndarray, features: list[str], record_ids: list[str], base_value: float
    ):
        self.values = values
        self.features = list(features)
        self.index = {rid: i for i, rid in enumerate(record_ids)}
        self.base_value = base_value

    @classmethod
    def load(cls, path: Path) -> PrecomputedShap:
        z = np.load(path, allow_pickle=True)
        return cls(
            z["values"],
            [str(f) for f in z["features"]],
            [str(r) for r in z["record_id"]],
            float(z["base_value"]),
        )

    def row(self, record_id: str) -> dict[str, float] | None:
        i = self.index.get(record_id)
        if i is None:
            return None
        return dict(zip(self.features, self.values[i].tolist(), strict=False))


def contributions(
    shap_row: dict[str, float], record_values: pd.Series | None, top: int = 8
) -> list[dict[str, Any]]:
    items = sorted(shap_row.items(), key=lambda kv: abs(kv[1]), reverse=True)[:top]
    out = []
    for feat, val in items:
        v = None
        if record_values is not None and feat in record_values.index:
            raw = record_values[feat]
            v = None if pd.isna(raw) else (raw.item() if hasattr(raw, "item") else raw)
        out.append({"feature": feat, "shap": float(val), "value": v})
    return out


def with_engineered(features_row: pd.DataFrame) -> pd.Series:
    """One-row frame of allow-listed source features -> Series incl. engineered values."""
    eng = engineer(features_row)
    return pd.concat([features_row.iloc[0], eng.iloc[0]])


def phrases(
    contribs: list[dict[str, Any]], rules: LanguageRules, reference: dict[str, float], top: int = 5
) -> list[dict[str, Any]]:
    return render_local(contribs, rules, top=top, reference=reference)


def explain_hypothetical(pipeline, X_one: pd.DataFrame, seed: int) -> dict[str, float]:
    """On-demand SHAP for one validated hypothetical record (same explainer as `ssn explain`)."""
    from ssn.explain.shap_explain import explain_pipeline

    res = explain_pipeline(pipeline, X_one, seed=seed)
    return res.per_source.iloc[0].to_dict()
