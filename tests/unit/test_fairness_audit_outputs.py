from __future__ import annotations

import numpy as np
import pandas as pd

from ssn.config import load
from ssn.fairness import audit as A
from ssn.fairness import mitigate as M
from ssn.features import allowlist as al


def _cohort(n=300, seed=3):
    rng = np.random.default_rng(seed)
    ids = [f"R{i:08x}" for i in range(n)]
    y = rng.integers(0, 2, n)
    score = np.clip(0.35 * y + rng.normal(0.35, 0.2, n), 0, 1)
    scores = pd.DataFrame({"record_id": ids, "score": score, "is_dropout": y})
    labels = pd.DataFrame(
        {
            "record_id": ids,
            "is_dropout": y,
            "Target": np.where(y == 1, "Dropout", "Graduate"),
            "Gender": rng.integers(0, 2, n),
            "Age at enrollment": rng.integers(17, 60, n),
        }
    )
    return scores, labels


def test_run_audit_outputs_are_aggregate_only(tmp_path):
    cfg = load("configs/base.yaml", set_seeds=False)
    allow = al.load("configs/features.yaml")
    scores, labels = _cohort()
    out = A.run_audit(scores, labels, cfg, allow, threshold=0.6, k=20, out_dir=tmp_path)
    text = (tmp_path / "group_metrics.json").read_text()
    assert "record_id" not in text and "R00000001" not in text
    groups = pd.read_csv(tmp_path / "group_metrics.csv")
    assert set(groups["attribute"]) == {"gender", "age_band"}
    assert set(groups["operating_point"]) == {"threshold", "top_k=20"}
    assert {"n", "reliable", "selection_rate", "tpr", "fpr", "brier", "base_rate"} <= set(
        groups.columns
    )
    assert set(groups.loc[groups.attribute == "gender", "group"]) <= {"male", "female"}
    summ = pd.DataFrame(out["attribute_summary"])
    assert {"dp_difference", "di_ratio", "eo_difference", "eq_odds_max_diff"} <= set(summ.columns)
    assert (
        out["gender_encoding"] == {1: "male", 0: "female"}
        and out["gender_encoding_verified"] is True
    )
    assert (tmp_path / "selection_rates.png").exists() and (
        tmp_path / "group_calibration.csv"
    ).exists()


def test_small_groups_are_flagged_in_audit(tmp_path):
    cfg = load("configs/base.yaml", set_seeds=False)
    allow = al.load("configs/features.yaml")
    scores, labels = _cohort(n=80)
    labels["Age at enrollment"] = np.where(
        np.arange(80) < 5, 50, 18
    )  # 5 mature students -> unreliable band
    A.run_audit(scores, labels, cfg, allow, threshold=0.6, k=10, out_dir=tmp_path)
    groups = pd.read_csv(tmp_path / "group_metrics.csv")
    small = groups[(groups.attribute == "age_band") & (groups.group == "35+")]
    assert (~small["reliable"]).all() and (small["n"] == 5).all()


def test_reweighting_weights_balance_group_label_mass():
    g = pd.Series(["a"] * 80 + ["b"] * 20)
    y = np.array([1] * 40 + [0] * 40 + [1] * 5 + [0] * 15)
    w = M.reweight_sample_weights(g, y)
    df = pd.DataFrame({"g": g, "y": y, "w": w})
    mass = df.groupby(["g", "y"])["w"].sum()
    assert np.allclose(mass.values, mass.values[0])  # equal weighted mass per (group, label)
    assert np.isclose(w.mean(), 1.0)


def test_group_thresholds_equalise_selection_rate():
    rng = np.random.default_rng(0)
    s = rng.random(400)
    g = pd.Series(["x"] * 300 + ["y"] * 100)
    thr = M.group_thresholds_equal_selection(s, g, k_total=40)
    pred = M.apply_group_thresholds(s, g, thr)
    assert pred[:300].sum() == 30 and pred[300:].sum() == 10
