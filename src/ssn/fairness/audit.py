"""Fairness audit of the final model on the test cohort (T061).

Inputs: final scores (evaluation-only file), evaluator labels + sensitive columns, manifest
threshold. Groups: gender (verified encoding) and age band; other attributes require documented
justification (PROJECT_DECISIONS). Outputs are AGGREGATE only: no record_id leaves this module.
Predictions are evaluated at the manifest threshold AND at top-K, because the tool operates as a
ranked outreach list.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from ssn.config import Config  # noqa: E402
from ssn.fairness import metrics as FM  # noqa: E402
from ssn.fairness.groups import group_frame  # noqa: E402
from ssn.features.allowlist import Allowlist  # noqa: E402
from ssn.modeling import evaluate as EV  # noqa: E402

RECORD_ID = "record_id"
IS_DROPOUT = "is_dropout"


def _group_calibration(y, s, groups: pd.Series, min_n: int, n_bins: int = 5) -> pd.DataFrame:
    rows = []
    for g in sorted(groups.unique()):
        m = (groups == g).to_numpy()
        if m.sum() < min_n:
            continue
        rel = EV.reliability_table(y[m], s[m], n_bins=n_bins)
        rel.insert(0, "group", g)
        rows.append(rel)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def run_audit(
    scores: pd.DataFrame,
    labels: pd.DataFrame,
    cfg: Config,
    allow: Allowlist,
    threshold: float,
    k: int,
    out_dir: Path,
) -> dict[str, Any]:
    df = scores.merge(labels, on=RECORD_ID, how="inner", suffixes=("", "_lbl"))
    if IS_DROPOUT + "_lbl" in df.columns:
        assert (df[IS_DROPOUT] == df[IS_DROPOUT + "_lbl"]).all(), (
            "label mismatch between scores and evaluator file"
        )
        df = df.drop(columns=[IS_DROPOUT + "_lbl"])
    y = df[IS_DROPOUT].to_numpy().astype(int)
    s = df["score"].to_numpy(dtype=float)
    pred_thr = (s >= threshold).astype(int)
    pred_k = EV.top_k_mask(s, k).astype(int)
    groups = group_frame(df, cfg, allow)
    min_n = int(cfg.get("fairness.min_group_size"))

    table_thr, summary_thr = FM.audit(y, s, pred_thr, groups, min_n)
    table_k, summary_k = FM.audit(y, s, pred_k, groups, min_n)
    table_thr.insert(1, "operating_point", "threshold")
    table_k.insert(1, "operating_point", f"top_k={k}")
    summary_thr.insert(1, "operating_point", "threshold")
    summary_k.insert(1, "operating_point", f"top_k={k}")
    table = pd.concat([table_thr, table_k], ignore_index=True)
    summary = pd.concat([summary_thr, summary_k], ignore_index=True)

    calib = pd.concat(
        [
            _group_calibration(y, s, groups[a].astype(str), min_n).assign(attribute=a)
            for a in groups.columns
        ],
        ignore_index=True,
    )
    assert RECORD_ID not in table.columns and RECORD_ID not in summary.columns

    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_dir / "group_metrics.csv", index=False)
    summary.to_csv(out_dir / "attribute_summary.csv", index=False)
    calib.to_csv(out_dir / "group_calibration.csv", index=False)
    payload = {
        "cohort": "held-out test split (evaluator-only labels)",
        "n": int(len(df)),
        "threshold": float(threshold),
        "k": int(k),
        "min_group_size": min_n,
        "attributes": list(groups.columns),
        "reference_group_rule": cfg.get("fairness.reference_group"),
        "groups": table.to_dict(orient="records"),
        "attribute_summary": summary.to_dict(orient="records"),
        "gender_encoding": {int(kk): v for kk, v in allow.columns["Gender"]["codes"].items()},
        "gender_encoding_verified": bool(allow.columns["Gender"].get("encoding_verified")),
        "note": (
            "Aggregate audit only. Sensitive attributes are never model inputs or adviser-facing "
            "reasons. Metrics within a tolerance do not establish fairness; see "
            "reports/bias_fairness_analysis.md."
        ),
    }
    (out_dir / "group_metrics.json").write_text(
        json.dumps(payload, indent=2, default=_json_default) + "\n"
    )
    fig_selection_rates(table_thr, table_k, min_n, out_dir / "selection_rates.png")
    fig_group_calibration(calib, out_dir / "group_calibration.png")
    return payload


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return str(o)


def fig_selection_rates(t_thr: pd.DataFrame, t_k: pd.DataFrame, min_n: int, path: Path) -> Path:
    attrs = list(t_thr["attribute"].unique())
    fig, axes = plt.subplots(2, len(attrs), figsize=(5.5 * len(attrs), 7), squeeze=False)
    for j, attr in enumerate(attrs):
        for i, (title, t) in enumerate((("at threshold", t_thr), ("at top-K", t_k))):
            sub = t[t["attribute"] == attr]
            ax = axes[i, j]
            x = np.arange(len(sub))
            colors = ["#4c72b0" if r else "#bbbbbb" for r in sub["reliable"]]
            ax.bar(x - 0.2, sub["selection_rate"], 0.2, color=colors, label="selection rate")
            ax.bar(x, sub["tpr"], 0.2, color="#55a868", alpha=0.8, label="TPR")
            ax.bar(x + 0.2, sub["fpr"], 0.2, color="#c44e52", alpha=0.8, label="FPR")
            ax.set_xticks(
                x,
                [f"{g}\n(n={n})" for g, n in zip(sub["group"], sub["n"], strict=False)],
                fontsize=8,
            )
            ax.set_ylim(0, 1)
            ax.set_title(f"{attr} — {title} (grey = n<{min_n})", fontsize=9)
            if i == 0 and j == 0:
                ax.legend(fontsize=7)
    fig.suptitle(
        "Group selection rate, TPR, FPR — final model, test cohort (aggregate audit)", fontsize=11
    )
    fig.text(
        0.01,
        0.005,
        "Source: UCI 697, held-out test split. `python -m ssn fairness audit`.",
        fontsize=7,
        color="gray",
    )
    fig.tight_layout(rect=(0, 0.02, 1, 0.96))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def fig_group_calibration(calib: pd.DataFrame, path: Path) -> Path:
    if calib.empty:
        return path
    attrs = list(calib["attribute"].unique())
    fig, axes = plt.subplots(1, len(attrs), figsize=(5.5 * len(attrs), 4.5), squeeze=False)
    for ax, attr in zip(axes[0], attrs, strict=False):
        ax.plot([0, 1], [0, 1], color="gray", ls="--", lw=1)
        for g, sub in calib[calib["attribute"] == attr].groupby("group"):
            sub = sub.dropna(subset=["mean_score", "observed_rate"])
            ax.plot(
                sub["mean_score"],
                sub["observed_rate"],
                marker="o",
                ms=4,
                label=f"{g} (n={int(sub['n'].sum())})",
            )
        ax.set_xlabel("mean predicted score (bin)")
        ax.set_ylabel("observed dropout rate")
        ax.set_title(f"Group calibration — {attr} (reliable groups only)", fontsize=9)
        ax.legend(fontsize=7)
    fig.text(
        0.01,
        0.005,
        "Source: UCI 697, held-out test split. `python -m ssn fairness audit`.",
        fontsize=7,
        color="gray",
    )
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path
