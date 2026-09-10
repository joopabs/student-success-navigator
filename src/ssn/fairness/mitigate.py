"""Mitigation experiment (T062, research R-15), evaluated on TRAINING out-of-fold predictions only.

(a) Reweighting: refit the tuned pipeline with sample weights that equalise (group x label) mass
    for the gender attribute. Changes the model.
(b) Group-specific thresholds: keep the model, pick per-group thresholds so that each gender group
    is selected at the same rate within a fixed total K. Uses the sensitive attribute at decision
    time, so it is REPORTED but NOT deployed (constitution Principle X).

The held-out test set is not touched: it has been evaluated once and mitigations are experiments.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone

from ssn.config import Config
from ssn.fairness import metrics as FM
from ssn.fairness.groups import group_frame
from ssn.features.allowlist import Allowlist
from ssn.features.preprocess import project_for_model
from ssn.modeling import evaluate as EV
from ssn.modeling.cv import make_cv
from ssn.modeling.threshold import capacity_threshold, k_for_cohort

IS_DROPOUT = "is_dropout"


def reweight_sample_weights(groups: pd.Series, y: np.ndarray) -> np.ndarray:
    """w = 1 / P(group, label) normalised to mean 1 (Kamiran & Calders reweighing)."""
    df = pd.DataFrame({"g": groups.astype(str).to_numpy(), "y": y})
    joint = df.groupby(["g", "y"]).size() / len(df)
    w = 1.0 / df.set_index(["g", "y"]).index.map(joint).to_numpy()
    return w / w.mean()


def oof_with_weights(
    pipeline, X: pd.DataFrame, y: np.ndarray, weights: np.ndarray | None, cfg: Config
) -> np.ndarray:
    scores = np.full(len(X), np.nan)
    for tr, va in make_cv(cfg).split(X, y):
        model = clone(pipeline)
        if weights is not None:
            model.fit(X.iloc[tr], y[tr], clf__sample_weight=weights[tr])
        else:
            model.fit(X.iloc[tr], y[tr])
        scores[va] = model.predict_proba(X.iloc[va])[:, 1]
    return scores


def group_thresholds_equal_selection(
    scores: np.ndarray, groups: pd.Series, k_total: int
) -> dict[str, float]:
    """Per-group thresholds so every group is selected at the same rate, summing to ~k_total."""
    g = groups.astype(str).to_numpy()
    rate = k_total / len(scores)
    out = {}
    for name in np.unique(g):
        m = g == name
        k_g = max(1, int(round(rate * m.sum())))
        out[str(name)] = capacity_threshold(scores[m], k_g)
    return out


def apply_group_thresholds(
    scores: np.ndarray, groups: pd.Series, thresholds: dict[str, float]
) -> np.ndarray:
    g = groups.astype(str).to_numpy()
    return np.array([int(s >= thresholds[str(gg)]) for s, gg in zip(scores, g, strict=False)])


def _row(
    name: str, y, s, pred, groups: pd.DataFrame, min_n: int, k: int, deployable: bool, note: str
) -> dict[str, Any]:
    _, summary = FM.audit(y, s, pred, groups, min_n)
    sm = summary.set_index("attribute")
    return {
        "variant": name,
        "deployable": deployable,
        "pr_auc": EV.pr_auc(y, s),
        "recall_at_k": EV.recall_at_k(y, s, k),
        "precision_at_k": EV.precision_at_k(y, s, k),
        "brier": EV.brier(y, s),
        "n_selected": int(pred.sum()),
        "gender_dp_difference": float(sm.loc["gender", "dp_difference"])
        if "gender" in sm.index
        else np.nan,
        "gender_di_ratio": float(sm.loc["gender", "di_ratio"]) if "gender" in sm.index else np.nan,
        "gender_eo_difference": float(sm.loc["gender", "eo_difference"])
        if "gender" in sm.index
        else np.nan,
        "age_band_dp_difference": float(sm.loc["age_band", "dp_difference"])
        if "age_band" in sm.index
        else np.nan,
        "age_band_eo_difference": float(sm.loc["age_band", "eo_difference"])
        if "age_band" in sm.index
        else np.nan,
        "note": note,
    }


def run_mitigation(
    train: pd.DataFrame,
    pipeline,
    baseline_oof: pd.DataFrame,
    cfg: Config,
    allow: Allowlist,
    n_cohort: int,
    out_dir: Path,
) -> pd.DataFrame:
    X = project_for_model(train, allow)
    y = train[IS_DROPOUT].to_numpy().astype(int)
    groups = group_frame(train, cfg, allow)
    min_n = int(cfg.get("fairness.min_group_size"))
    k = k_for_cohort(int(cfg.get("capacity.k")), len(X), n_cohort)

    s0 = baseline_oof.set_index("record_id").loc[train["record_id"], "score"].to_numpy()
    thr0 = capacity_threshold(s0, k)
    rows = [
        _row(
            "baseline (deployed)",
            y,
            s0,
            (s0 >= thr0).astype(int),
            groups,
            min_n,
            k,
            True,
            "tuned pipeline, capacity threshold on OOF scores",
        )
    ]

    w = reweight_sample_weights(groups["gender"], y)
    s1 = oof_with_weights(pipeline, X, y, w, cfg)
    thr1 = capacity_threshold(s1, k)
    rows.append(
        _row(
            "reweighting (gender x label)",
            y,
            s1,
            (s1 >= thr1).astype(int),
            groups,
            min_n,
            k,
            True,
            "refit with Kamiran-Calders reweighing on gender; changes the model; "
            "no sensitive input at inference",
        )
    )

    gt = group_thresholds_equal_selection(s0, groups["gender"], k)
    pred2 = apply_group_thresholds(s0, groups["gender"], gt)
    rows.append(
        _row(
            "group thresholds (equal selection by gender)",
            y,
            s0,
            pred2,
            groups,
            min_n,
            k,
            False,
            f"per-group thresholds {json.dumps({kk: round(v, 4) for kk, v in gt.items()})}; "
            "uses gender at decision time -> NOT deployed",
        )
    )

    table = pd.DataFrame(rows)
    base = table.iloc[0]
    for col in [
        "pr_auc",
        "recall_at_k",
        "brier",
        "gender_dp_difference",
        "gender_eo_difference",
        "age_band_dp_difference",
    ]:
        table[f"delta_{col}"] = table[col] - base[col]
    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_dir / "mitigation_comparison.csv", index=False)
    return table
