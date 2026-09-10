"""SHAP explanations for the saved final pipeline (T058, research R-12).

The persisted model is a CalibratedClassifierCV ensemble; each member wraps `pre -> clf`. SHAP is
computed on each member's fitted base estimator (TreeExplainer for tree models, LinearExplainer
for logistic regression) in that member's own transformed space, aggregated back to SOURCE
columns (one-hot columns summed per original column), then averaged across members. Explanations
therefore describe the uncalibrated ensemble-average contributions, not the calibrated
probability, and this is stated in `method.json`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import shap  # noqa: E402
from sklearn.inspection import permutation_importance  # noqa: E402

from ssn.features.engineering import ENGINEERED_NAMES  # noqa: E402

_ONEHOT_SUFFIX = re.compile(r"_(-?\d+(?:\.\d+)?)$")


def source_column(transformed_name: str) -> str:
    """Map a transformed name back to its source column.

    'cat__Course_9130' -> 'Course'; 'num__sem1_load' -> 'sem1_load';
    'bin__Displaced' -> 'Displaced'.
    """
    name = transformed_name.split("__", 1)[1] if "__" in transformed_name else transformed_name
    if transformed_name.startswith("cat__"):
        name = _ONEHOT_SUFFIX.sub("", name)
    return name


def base_members(pipeline) -> list[Any]:
    """Fitted `pre -> clf` pipelines inside a CalibratedClassifierCV, or [pipeline] otherwise."""
    if hasattr(pipeline, "calibrated_classifiers_"):
        return [c.estimator for c in pipeline.calibrated_classifiers_]
    return [pipeline]


def _explainer_for(clf, Xt: np.ndarray):
    name = type(clf).__name__
    if name in {
        "RandomForestClassifier",
        "HistGradientBoostingClassifier",
        "GradientBoostingClassifier",
    }:
        return shap.TreeExplainer(clf), "shap.TreeExplainer"
    if name == "LogisticRegression":
        return shap.LinearExplainer(clf, Xt), "shap.LinearExplainer"
    return None, "permutation_importance (fallback)"


def _positive_class(values) -> np.ndarray:
    arr = np.asarray(values)
    if arr.ndim == 3:  # (n, features, classes)
        return arr[:, :, 1]
    if isinstance(values, list):  # older shap: list per class
        return np.asarray(values[1])
    return arr


@dataclass
class ShapResult:
    per_source: (
        pd.DataFrame
    )  # rows = records, columns = source features (aggregated, member-averaged)
    base_value: float
    method: str
    members: int
    transformed_names_example: list[str]


def explain_pipeline(
    pipeline, X: pd.DataFrame, y: pd.Series | None = None, seed: int = 42
) -> ShapResult:
    members = base_members(pipeline)
    agg_frames = []
    base_values = []
    method = None
    for member in members:
        pre, clf = member.named_steps["pre"], member.named_steps["clf"]
        Xt = np.asarray(pre.transform(X))
        names = [str(n) for n in pre.get_feature_names_out()]
        explainer, method = _explainer_for(clf, Xt)
        if explainer is not None:
            sv = _positive_class(explainer.shap_values(Xt))
            ev = np.asarray(explainer.expected_value)
            base_values.append(float(ev[1] if ev.ndim else ev))
        else:  # documented fallback: permutation importance broadcast as a global-only signal
            if y is None:
                raise ValueError("permutation fallback needs y")
            pi = permutation_importance(
                member, X, y, scoring="average_precision", n_repeats=5, random_state=seed
            )
            sv = np.tile(pi.importances_mean, (len(X), 1))
            names = list(X.columns)
            base_values.append(float("nan"))
        frame = pd.DataFrame(sv, columns=names, index=X.index)
        frame.columns = [source_column(c) for c in frame.columns]
        agg_frames.append(frame.T.groupby(level=0).sum().T)
    per_source = sum(agg_frames) / len(agg_frames)
    return ShapResult(
        per_source=per_source,
        base_value=float(np.nanmean(base_values)),
        method=method or "unknown",
        members=len(members),
        transformed_names_example=names[:5],
    )


def global_importance(res: ShapResult) -> pd.DataFrame:
    mean_abs = res.per_source.abs().mean().sort_values(ascending=False)
    mean_signed = res.per_source.mean()
    out = pd.DataFrame(
        {
            "feature": mean_abs.index,
            "mean_abs_shap": mean_abs.values,
            "mean_signed_shap": mean_signed.loc[mean_abs.index].values,
        }
    )
    out["engineered"] = out["feature"].isin(ENGINEERED_NAMES)
    return out.reset_index(drop=True)


def fig_global_bar(imp: pd.DataFrame, path: Path, top: int = 20) -> Path:
    t = imp.head(top).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.35 * len(t) + 1.5))
    colors = ["#dd8452" if e else "#4c72b0" for e in t["engineered"]]
    ax.barh(t["feature"], t["mean_abs_shap"], color=colors)
    ax.set_xlabel("mean |SHAP| (uncalibrated score units, member-averaged)")
    ax.set_title(
        f"Global feature importance, final model, test cohort (top {top}; orange = engineered)"
    )
    fig.text(
        0.01,
        0.005,
        "Source: UCI 697, test cohort features (no labels used). `python -m ssn explain`.",
        fontsize=7,
        color="gray",
    )
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def fig_beeswarm(res: ShapResult, X_raw: pd.DataFrame, path: Path, top: int = 15) -> Path:
    imp = global_importance(res)["feature"].head(top).tolist()
    vals = res.per_source[imp].to_numpy()
    feats = pd.DataFrame(
        {c: pd.to_numeric(X_raw[c], errors="coerce") if c in X_raw.columns else np.nan for c in imp}
    )
    plt.figure(figsize=(9, 0.4 * top + 1.5))
    shap.summary_plot(
        vals, features=feats, feature_names=imp, show=False, max_display=top, plot_size=None
    )
    plt.title(
        "SHAP beeswarm (aggregated per source feature; colour = raw value where numeric)",
        fontsize=10,
    )
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()
    return path


def local_examples(
    res: ShapResult,
    scores: pd.DataFrame,
    X_raw: pd.DataFrame,
    threshold: float,
    record_ids: pd.Series,
    top: int = 5,
) -> list[dict[str, Any]]:
    """Representative TP / FP / FN / TN records chosen by score extremity (synthetic ids only)."""
    from ssn.features.engineering import engineer

    X_raw = pd.concat([X_raw, engineer(X_raw)], axis=1)  # engineered values for phrase direction
    df = scores.copy()
    df["pred"] = (df["score"] >= threshold).astype(int)
    picks = {
        "true_positive": df[(df.pred == 1) & (df.is_dropout == 1)]
        .sort_values("score", ascending=False)
        .head(1),
        "false_positive": df[(df.pred == 1) & (df.is_dropout == 0)]
        .sort_values("score", ascending=False)
        .head(1),
        "false_negative": df[(df.pred == 0) & (df.is_dropout == 1)]
        .sort_values("score", ascending=False)
        .head(1),
        "true_negative": df[(df.pred == 0) & (df.is_dropout == 0)].sort_values("score").head(1),
    }
    pos = {rid: i for i, rid in enumerate(record_ids)}
    out = []
    for kind, row in picks.items():
        if row.empty:
            out.append({"case": kind, "available": False})
            continue
        rid = row.iloc[0]["record_id"]
        i = pos[rid]
        contrib = res.per_source.iloc[i].sort_values(key=np.abs, ascending=False).head(top)
        out.append(
            {
                "case": kind,
                "available": True,
                "record_id": rid,
                "score": float(row.iloc[0]["score"]),
                "band": row.iloc[0].get("band", None),
                "outcome_is_dropout": int(row.iloc[0]["is_dropout"]),
                "top_contributions": [
                    {
                        "feature": f,
                        "shap": float(v),
                        "value": (None if f not in X_raw.columns else _py(X_raw.iloc[i][f])),
                    }
                    for f, v in contrib.items()
                ],
            }
        )
    return out


def _py(v):
    v = v.item() if hasattr(v, "item") else v
    return None if isinstance(v, float) and np.isnan(v) else v


def write_outputs(
    res: ShapResult,
    imp: pd.DataFrame,
    examples: list[dict[str, Any]],
    record_ids: pd.Series,
    out_dir: Path,
    extra_method: dict[str, Any],
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    p = out_dir / "shap_global_importance.csv"
    imp.to_csv(p, index=False)
    written.append(p)
    p = out_dir / "shap_values_test.npz"
    np.savez_compressed(
        p,
        values=res.per_source.to_numpy(),
        features=np.array(res.per_source.columns, dtype=object),
        record_id=np.array(record_ids, dtype=object),
        base_value=res.base_value,
    )
    written.append(p)
    p = out_dir / "shap_local_examples.json"
    p.write_text(json.dumps(examples, indent=2, default=str) + "\n")
    written.append(p)
    p = out_dir / "method.json"
    p.write_text(
        json.dumps(
            {
                "method": res.method,
                "ensemble_members": res.members,
                "base_value_mean": res.base_value,
                "aggregation": (
                    "one-hot columns summed per source column; "
                    "averaged over calibrated ensemble members"
                ),
                "explains": (
                    "uncalibrated base-estimator score contributions, "
                    "not the calibrated probability"
                ),
                **extra_method,
            },
            indent=2,
        )
        + "\n"
    )
    written.append(p)
    return written
