"""Partial dependence and ICE for suitable continuous raw features (T059).

Suitability rule (configs/base.yaml explain.pdp_min_distinct_values): a raw allow-listed numeric
column with at least that many distinct values in the cohort. Engineered features are computed
inside the pipeline and cannot be varied independently of their inputs, so they are excluded here
and explained through SHAP instead; the exclusion reason is recorded.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.inspection import PartialDependenceDisplay  # noqa: E402

from ssn.features.allowlist import Allowlist  # noqa: E402
from ssn.features.engineering import ENGINEERED_NAMES  # noqa: E402


def select_features(X: pd.DataFrame, allow: Allowlist, min_distinct: int) -> pd.DataFrame:
    rows = []
    for col in X.columns:
        meta = allow.columns.get(col, {})
        n = int(X[col].nunique())
        if meta.get("dtype") != "numeric":
            reason = f"not continuous (dtype {meta.get('dtype')})"
            ok = False
        elif n < min_distinct:
            reason = f"only {n} distinct values (< {min_distinct})"
            ok = False
        else:
            reason, ok = "", True
        rows.append({"feature": col, "n_distinct": n, "included": ok, "reason_excluded": reason})
    for name in ENGINEERED_NAMES:
        rows.append(
            {
                "feature": name,
                "n_distinct": None,
                "included": False,
                "reason_excluded": (
                    "engineered inside the pipeline; cannot be varied independently of its "
                    "inputs (see SHAP)"
                ),
            }
        )
    return pd.DataFrame(rows)


def plot_pdp_ice(
    pipeline, X: pd.DataFrame, features: list[str], out_dir: Path, seed: int, n_ice: int = 60
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    # sklearn refuses integer-typed PDP features; cast the continuous columns to float. Categorical
    # code columns keep their integer dtype so the fitted one-hot encoder still recognises them.
    X = X.astype({c: float for c in features})
    sample = X.sample(n=min(n_ice, len(X)), random_state=seed)
    for feat in features:
        fig, ax = plt.subplots(figsize=(6, 4.2))
        PartialDependenceDisplay.from_estimator(
            pipeline,
            X,
            [feat],
            kind="both",
            subsample=len(sample),
            random_state=seed,
            ax=ax,
            response_method="predict_proba",
            ice_lines_kw={"alpha": 0.15, "linewidth": 0.6},
            pd_line_kw={"color": "#c44e52", "linewidth": 2},
        )
        ax.set_title(f"PDP (red) and ICE ({len(sample)} test records) for {feat}", fontsize=10)
        ax.set_ylabel("calibrated dropout support-priority score")
        fig.text(
            0.01,
            0.005,
            "Source: UCI 697, test cohort features. `python -m ssn explain`.",
            fontsize=7,
            color="gray",
        )
        fig.tight_layout(rect=(0, 0.02, 1, 1))
        safe = feat.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
        p = out_dir / f"pdp_ice_{safe}.png"
        fig.savefig(p, dpi=120)
        plt.close(fig)
        written.append(p)
    return written
