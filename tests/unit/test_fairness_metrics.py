from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ssn.fairness import metrics as FM

# Hand-worked example. Two groups A (n=6) and B (n=4).
Y = np.array([1, 1, 0, 0, 1, 0, 1, 0, 0, 0])
P = np.array([1, 1, 1, 0, 0, 0, 1, 1, 0, 0])  # predictions
S = np.array([0.9, 0.8, 0.7, 0.2, 0.4, 0.1, 0.95, 0.6, 0.3, 0.2])
G = pd.Series(["A"] * 6 + ["B"] * 4)


def test_group_table_hand_computed():
    t = FM.group_table(Y, S, P, G, min_group_size=4).set_index("group")
    # A: y=[1,1,0,0,1,0], p=[1,1,1,0,0,0] -> selection 3/6, tpr 2/3, fpr 1/3
    assert t.loc["A", "n"] == 6 and t.loc["A", "selection_rate"] == pytest.approx(0.5)
    assert t.loc["A", "tpr"] == pytest.approx(2 / 3) and t.loc["A", "fpr"] == pytest.approx(1 / 3)
    assert t.loc["A", "base_rate"] == pytest.approx(0.5)
    # B: y=[1,0,0,0], p=[1,1,0,0] -> selection 2/4, tpr 1/1, fpr 1/3
    assert t.loc["B", "selection_rate"] == pytest.approx(0.5) and t.loc["B", "tpr"] == 1.0
    assert t.loc["B", "fpr"] == pytest.approx(1 / 3)
    assert bool(t.loc["A", "reliable"]) and bool(t.loc["B", "reliable"])


def test_attribute_summary_differences_and_ratios():
    t = FM.group_table(Y, S, P, G, min_group_size=4)
    s = FM.attribute_summary("g", t)
    assert s.reference_group == "A"  # largest group
    assert s.dp_difference == pytest.approx(0.0)  # both selection rates 0.5
    assert s.di_ratio == pytest.approx(1.0)
    assert s.eo_difference == pytest.approx(1.0 - 2 / 3)
    assert s.eq_odds_max_diff == pytest.approx(max(1.0 - 2 / 3, 0.0))
    assert s.n_reliable_groups == 2


def test_small_group_flagged_unreliable_and_excluded_from_summary():
    g = pd.Series(["A"] * 8 + ["B"] * 2)
    t = FM.group_table(Y, S, P, g, min_group_size=3).set_index("group")
    assert bool(t.loc["A", "reliable"]) and not bool(t.loc["B", "reliable"])
    s = FM.attribute_summary("g", t.reset_index())
    assert s.n_reliable_groups == 1 and np.isnan(
        s.dp_difference
    )  # cannot compare with one reliable group


def test_di_ratio_when_a_group_has_zero_selection():
    p = np.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 0])  # B selects nobody
    t = FM.group_table(Y, S, p, G, min_group_size=4)
    s = FM.attribute_summary("g", t)
    assert s.di_ratio == pytest.approx(0.0) and s.dp_difference == pytest.approx(0.5)


def test_audit_returns_per_attribute_tables():
    groups = pd.DataFrame({"g": G, "h": pd.Series(["x", "y"] * 5)})
    table, summary = FM.audit(Y, S, P, groups, min_group_size=2)
    assert set(table["attribute"]) == {"g", "h"} and len(summary) == 2
    assert {
        "attribute",
        "reference_group",
        "dp_difference",
        "di_ratio",
        "eo_difference",
        "eq_odds_max_diff",
    } <= set(summary.columns)
