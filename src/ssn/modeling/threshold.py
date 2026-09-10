"""Capacity-aware threshold and risk bands from OOF scores (T051, research R-09).

The operating threshold is the OOF score at which the selection rate equals K / n_cohort, where
K is the ILLUSTRATIVE outreach capacity (per_week x window_weeks). Bands are OOF score quantiles
with supportive names. Alternatives (F1-optimal, precision-floor, 0.5) are reported with their
false-positive / false-negative trade-offs so the choice is transparent. Never uses test data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ssn.config import Config
from ssn.modeling import evaluate as EV


def k_for_cohort(k: int, n: int, n_cohort: int) -> int:
    """K scaled from the deployment cohort to a set of n rows (min 1)."""
    return max(1, int(round(k * n / n_cohort)))


def capacity_threshold(scores, k: int) -> float:
    """Score of the k-th highest OOF score: predicting score >= threshold selects ~k rows."""
    s = np.sort(np.asarray(scores, dtype=float))[::-1]
    k = int(min(max(k, 1), len(s)))
    return float(s[k - 1])


def f1_optimal_threshold(y, scores) -> float:
    curve = EV.pr_curve(y, scores)
    f1 = (
        2
        * curve["precision"]
        * curve["recall"]
        / (curve["precision"] + curve["recall"]).replace(0, np.nan)
    )
    return float(curve.loc[f1.idxmax(), "threshold"])


def precision_floor_threshold(y, scores, floor: float) -> float | None:
    curve = EV.pr_curve(y, scores)
    ok = curve[curve["precision"] >= floor]
    if ok.empty:
        return None
    return float(ok.loc[ok["recall"].idxmax(), "threshold"])


def tradeoff_row(name: str, y, scores, thr: float) -> dict[str, Any]:
    m = EV.threshold_metrics(y, scores, thr)
    c = EV.confusion_at_threshold(y, scores, thr)
    return {
        "rule": name,
        "threshold": float(thr),
        "n_selected": m["n_predicted_positive"],
        "selection_rate": m["n_predicted_positive"] / len(np.asarray(y)),
        "precision": m["precision"],
        "recall": m["recall"],
        "f1": m["f1"],
        "false_positives": c.fp,
        "false_negatives": c.fn,
        "true_positives": c.tp,
    }


def build_bands(scores, k: int, multiplier: float, names: list[str]) -> list[dict[str, Any]]:
    n = len(scores)
    top = capacity_threshold(scores, k)
    mid = capacity_threshold(scores, min(n, int(round(k * multiplier))))
    return [
        {"name": names[0], "lower": top, "upper": 1.0, "rule": "score >= capacity threshold"},
        {
            "name": names[1],
            "lower": mid,
            "upper": top,
            "rule": f"score >= threshold at {multiplier:g} x capacity selection rate",
        },
        {"name": names[2], "lower": 0.0, "upper": mid, "rule": "remaining scores"},
    ]


def assign_band(score: float, bands: list[dict[str, Any]]) -> str:
    for b in bands:  # bands ordered top -> bottom; lower bound inclusive
        if score >= b["lower"]:
            return b["name"]
    return bands[-1]["name"]


def run_threshold(
    oof: pd.DataFrame, cfg: Config, n_cohort: int, tables_dir: Path, precision_floor: float = 0.8
) -> dict[str, Any]:
    y = oof["y_true"].to_numpy().astype(int)
    s = oof["score"].to_numpy(dtype=float)
    n = len(s)
    K = int(cfg.get("capacity.k"))
    per_week = int(cfg.get("capacity.per_week"))
    windows = list(cfg.get("capacity.window_sensitivity_weeks"))
    k_train = k_for_cohort(K, n, n_cohort)
    thr = capacity_threshold(s, k_train)
    names = list(cfg.get("threshold.band_names"))
    mult = float(cfg.get("threshold.middle_band_selection_rate_multiplier"))
    bands = build_bands(s, k_train, mult, names)

    rows = [tradeoff_row("capacity (chosen)", y, s, thr)]
    rows.append(tradeoff_row("f1_optimal", y, s, f1_optimal_threshold(y, s)))
    pf = precision_floor_threshold(y, s, precision_floor)
    if pf is not None:
        rows.append(tradeoff_row(f"precision>={precision_floor:g}", y, s, pf))
    rows.append(tradeoff_row("0.5 (default)", y, s, 0.5))
    tradeoffs = pd.DataFrame(rows)

    sens = []
    for w in windows:
        kk = per_week * w
        kt = k_for_cohort(kk, n, n_cohort)
        sens.append(
            {
                "window_weeks": w,
                "capacity_k": kk,
                "k_scaled_to_train": kt,
                "recall_at_k": EV.recall_at_k(y, s, kt),
                "precision_at_k": EV.precision_at_k(y, s, kt),
                "share_of_dropouts_reached_illustrative": EV.recall_at_k(y, s, kt),
                "note": "ILLUSTRATIVE capacity; recall ceiling = k / positives",
            }
        )
    sensitivity = pd.DataFrame(sens)

    zero_positive = bool(EV.confusion_at_threshold(y, s, thr).tp == 0)
    result = {
        "rule": cfg.get("threshold.rule"),
        "capacity_per_week": per_week,
        "window_weeks": int(cfg.get("capacity.window_weeks")),
        "capacity_k": K,
        "capacity_illustrative": True,
        "n_cohort_expected": int(n_cohort),
        "n_oof_rows": int(n),
        "k_scaled_to_oof": int(k_train),
        "selection_rate": k_train / n,
        "threshold": thr,
        "bands": bands,
        "band_shares_oof": {
            b["name"]: float(np.mean([assign_band(v, bands) == b["name"] for v in s]))
            for b in bands
        },
        "tradeoffs": rows,
        "zero_predicted_positives": zero_positive,
        "source": "out-of-fold scores on the training split; test data not used",
    }
    tables_dir.mkdir(parents=True, exist_ok=True)
    (tables_dir / "threshold_and_bands.json").write_text(
        json.dumps(result, indent=2, default=float) + "\n"
    )
    tradeoffs.to_csv(tables_dir / "threshold_tradeoffs.csv", index=False)
    sensitivity.to_csv(tables_dir / "oof_recall_precision_at_k.csv", index=False)
    return result


def load_threshold(tables_dir: Path) -> dict[str, Any]:
    return json.loads((tables_dir / "threshold_and_bands.json").read_text())
