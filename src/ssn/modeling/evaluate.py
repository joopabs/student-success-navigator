"""Evaluation metrics (T042).

Ranking metrics (Recall@K, Precision@K) implement the outreach-capacity view: the top K scores are
the students an adviser would reach. Ties are broken by stable sort order (first occurrence wins),
which is deterministic for a fixed input order and documented here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)


def _arrays(y, score):
    y = np.asarray(y).astype(int)
    s = np.asarray(score, dtype=float)
    if y.shape != s.shape:
        raise ValueError("y and score must have the same shape")
    return y, s


def pr_auc(y, score) -> float:
    y, s = _arrays(y, score)
    return float(average_precision_score(y, s))


def roc_auc(y, score) -> float:
    y, s = _arrays(y, score)
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, s))


def top_k_mask(score, k: int) -> np.ndarray:
    """Boolean mask of the k highest scores; ties -> earliest index (stable mergesort)."""
    s = np.asarray(score, dtype=float)
    k = int(min(max(k, 0), len(s)))
    order = np.argsort(-s, kind="mergesort")
    mask = np.zeros(len(s), dtype=bool)
    mask[order[:k]] = True
    return mask


def recall_at_k(y, score, k: int) -> float:
    y, s = _arrays(y, score)
    pos = y.sum()
    if pos == 0:
        return float("nan")
    return float(y[top_k_mask(s, k)].sum() / pos)


def precision_at_k(y, score, k: int) -> float:
    y, s = _arrays(y, score)
    if k <= 0:
        return float("nan")
    m = top_k_mask(s, k)
    return float(y[m].sum() / m.sum())


def brier(y, score) -> float:
    y, s = _arrays(y, score)
    return float(brier_score_loss(y, s))


def expected_calibration_error(y, score, n_bins: int = 10) -> float:
    """Equal-width bins on [0, 1]; weighted mean |mean(y) - mean(score)| per bin."""
    y, s = _arrays(y, score)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(s, edges[1:-1], right=True), 0, n_bins - 1)
    ece = 0.0
    for b in range(n_bins):
        m = idx == b
        if m.any():
            ece += m.mean() * abs(y[m].mean() - s[m].mean())
    return float(ece)


def reliability_table(y, score, n_bins: int = 10) -> pd.DataFrame:
    y, s = _arrays(y, score)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(s, edges[1:-1], right=True), 0, n_bins - 1)
    rows = []
    for b in range(n_bins):
        m = idx == b
        rows.append(
            {
                "bin": b,
                "lower": edges[b],
                "upper": edges[b + 1],
                "n": int(m.sum()),
                "mean_score": float(s[m].mean()) if m.any() else np.nan,
                "observed_rate": float(y[m].mean()) if m.any() else np.nan,
            }
        )
    return pd.DataFrame(rows)


@dataclass(frozen=True)
class Confusion:
    tn: int
    fp: int
    fn: int
    tp: int

    def as_dict(self, prefix: str = "") -> dict[str, int]:
        return {
            f"{prefix}tn": self.tn,
            f"{prefix}fp": self.fp,
            f"{prefix}fn": self.fn,
            f"{prefix}tp": self.tp,
        }


def confusion_from_pred(y, pred) -> Confusion:
    y = np.asarray(y).astype(int)
    p = np.asarray(pred).astype(int)
    return Confusion(
        tn=int(((y == 0) & (p == 0)).sum()),
        fp=int(((y == 0) & (p == 1)).sum()),
        fn=int(((y == 1) & (p == 0)).sum()),
        tp=int(((y == 1) & (p == 1)).sum()),
    )


def confusion_at_threshold(y, score, threshold: float) -> Confusion:
    y, s = _arrays(y, score)
    return confusion_from_pred(y, s >= threshold)


def confusion_at_k(y, score, k: int) -> Confusion:
    y, s = _arrays(y, score)
    return confusion_from_pred(y, top_k_mask(s, k))


def threshold_metrics(y, score, threshold: float) -> dict[str, float]:
    y, s = _arrays(y, score)
    pred = (s >= threshold).astype(int)
    return {
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "accuracy": float((pred == y).mean()),
        "n_predicted_positive": int(pred.sum()),
    }


def metrics_table(
    y, score, *, threshold: float, k: int, k_values: dict[str, int] | None = None
) -> dict[str, float]:
    """All FR-012..FR-014 metrics for one set of scores. `k_values` adds Recall@K for other K."""
    y, s = _arrays(y, score)
    out: dict[str, float] = {
        "pr_auc": pr_auc(y, s),
        "roc_auc": roc_auc(y, s),
        "brier": brier(y, s),
        "ece": expected_calibration_error(y, s),
        "recall_at_k": recall_at_k(y, s, k),
        "precision_at_k": precision_at_k(y, s, k),
        "k": int(k),
    }
    out.update(
        {f"{name}_at_threshold": v for name, v in threshold_metrics(y, s, threshold).items()}
    )
    out.update(confusion_at_threshold(y, s, threshold).as_dict("thr_"))
    out.update(confusion_at_k(y, s, k).as_dict("topk_"))
    for label, kk in (k_values or {}).items():
        out[f"recall_at_{label}"] = recall_at_k(y, s, kk)
        out[f"precision_at_{label}"] = precision_at_k(y, s, kk)
    return out


def pr_curve(y, score) -> pd.DataFrame:
    y, s = _arrays(y, score)
    p, r, t = precision_recall_curve(y, s)
    return pd.DataFrame({"precision": p[:-1], "recall": r[:-1], "threshold": t})
