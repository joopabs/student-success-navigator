"""Group fairness metrics (T049), implemented with pandas/numpy (research R-13).

Per group: n, reliable flag, selection rate, TPR, FPR, Brier, base rate.
Per attribute: demographic-parity difference (max - min selection rate), disparate-impact ratio
(min / max selection rate), equal-opportunity difference (max - min TPR), equalized-odds max
difference (max of TPR and FPR ranges), computed over RELIABLE groups only, with the largest
group as reference.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ssn.modeling.evaluate import brier


@dataclass(frozen=True)
class AttributeSummary:
    attribute: str
    reference_group: str
    n_groups: int
    n_reliable_groups: int
    dp_difference: float
    di_ratio: float
    eo_difference: float
    eq_odds_max_diff: float
    max_brier_gap: float


def group_table(y, score, pred, groups: pd.Series, min_group_size: int) -> pd.DataFrame:
    y = np.asarray(y).astype(int)
    s = np.asarray(score, dtype=float)
    p = np.asarray(pred).astype(int)
    g = pd.Series(np.asarray(groups).astype(str))
    rows = []
    for name, idx in g.groupby(g).groups.items():
        idx = np.asarray(list(idx))
        yy, pp, ss = y[idx], p[idx], s[idx]
        pos, neg = (yy == 1), (yy == 0)
        rows.append(
            {
                "group": name,
                "n": int(len(idx)),
                "reliable": bool(len(idx) >= min_group_size),
                "base_rate": float(yy.mean()),
                "selection_rate": float(pp.mean()),
                "tpr": float(pp[pos].mean()) if pos.any() else np.nan,
                "fpr": float(pp[neg].mean()) if neg.any() else np.nan,
                "brier": float(brier(yy, ss)),
                "n_selected": int(pp.sum()),
                "n_positive": int(pos.sum()),
            }
        )
    return pd.DataFrame(rows).sort_values("n", ascending=False).reset_index(drop=True)


def attribute_summary(attribute: str, table: pd.DataFrame) -> AttributeSummary:
    rel = table[table["reliable"]]
    ref = str(table.iloc[0]["group"]) if len(table) else ""
    if len(rel) < 2:
        return AttributeSummary(
            attribute, ref, len(table), len(rel), np.nan, np.nan, np.nan, np.nan, np.nan
        )
    sel = rel["selection_rate"]
    tpr = rel["tpr"].dropna()
    fpr = rel["fpr"].dropna()
    di = float(sel.min() / sel.max()) if sel.max() > 0 else np.nan
    return AttributeSummary(
        attribute=attribute,
        reference_group=ref,
        n_groups=int(len(table)),
        n_reliable_groups=int(len(rel)),
        dp_difference=float(sel.max() - sel.min()),
        di_ratio=di,
        eo_difference=float(tpr.max() - tpr.min()) if len(tpr) >= 2 else np.nan,
        eq_odds_max_diff=float(
            max(
                tpr.max() - tpr.min() if len(tpr) >= 2 else 0.0,
                fpr.max() - fpr.min() if len(fpr) >= 2 else 0.0,
            )
        ),
        max_brier_gap=float(rel["brier"].max() - rel["brier"].min()),
    )


def audit(
    y, score, pred, groups: pd.DataFrame, min_group_size: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (per-group table with an `attribute` column, attribute-level summary table)."""
    tables, summaries = [], []
    for attr in groups.columns:
        t = group_table(y, score, pred, groups[attr], min_group_size)
        t.insert(0, "attribute", attr)
        tables.append(t)
        summaries.append(attribute_summary(attr, t).__dict__)
    return pd.concat(tables, ignore_index=True), pd.DataFrame(summaries)
