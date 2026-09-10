from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ssn.config import load
from ssn.modeling import threshold as TH


def test_k_for_cohort_scales_and_floors():
    assert TH.k_for_cohort(50, 3539, 885) == 200
    assert TH.k_for_cohort(50, 885, 885) == 50
    assert TH.k_for_cohort(1, 10, 885) == 1


def test_capacity_threshold_selects_k_rows():
    s = np.array([0.1, 0.9, 0.5, 0.7, 0.3])
    thr = TH.capacity_threshold(s, 2)
    assert thr == 0.7 and (s >= thr).sum() == 2
    assert TH.capacity_threshold(s, 99) == 0.1  # k clipped to n


def test_bands_are_monotone_and_assign_band_uses_lower_bounds():
    s = np.linspace(0, 1, 101)
    bands = TH.build_bands(s, k=10, multiplier=2.0, names=["top", "mid", "rest"])
    assert bands[0]["lower"] >= bands[1]["lower"] >= bands[2]["lower"] == 0.0
    assert bands[0]["upper"] == 1.0 and bands[1]["upper"] == bands[0]["lower"]
    assert TH.assign_band(1.0, bands) == "top"
    assert TH.assign_band(bands[0]["lower"], bands) == "top"  # inclusive lower bound
    assert TH.assign_band(bands[1]["lower"], bands) == "mid"
    assert TH.assign_band(0.0, bands) == "rest"


def test_run_threshold_selection_rate_matches_capacity(tmp_path):
    cfg = load("configs/base.yaml", set_seeds=False)
    rng = np.random.default_rng(0)
    n = 1000
    y = rng.integers(0, 2, size=n)
    score = np.clip(0.3 * y + rng.normal(0.4, 0.2, size=n), 0, 1)
    oof = pd.DataFrame(
        {
            "record_id": [f"R{i}" for i in range(n)],
            "fold": rng.integers(0, 5, n),
            "y_true": y,
            "score": score,
        }
    )
    res = TH.run_threshold(oof, cfg, n_cohort=885, tables_dir=tmp_path)
    k_expected = TH.k_for_cohort(cfg.get("capacity.k"), n, 885)
    assert res["k_scaled_to_oof"] == k_expected
    assert (score >= res["threshold"]).sum() == k_expected
    assert res["selection_rate"] == pytest.approx(k_expected / n)
    assert res["capacity_illustrative"] is True and res["zero_predicted_positives"] is False
    assert [b["name"] for b in res["bands"]] == cfg.get("threshold.band_names")
    assert (tmp_path / "threshold_and_bands.json").exists()
    trade = pd.read_csv(tmp_path / "threshold_tradeoffs.csv")
    assert {"capacity (chosen)", "f1_optimal", "0.5 (default)"} <= set(trade["rule"])
    assert {"false_positives", "false_negatives", "precision", "recall"} <= set(trade.columns)
    sens = pd.read_csv(tmp_path / "oof_recall_precision_at_k.csv")
    assert list(sens["window_weeks"]) == cfg.get("capacity.window_sensitivity_weeks")
    assert (sens["recall_at_k"].diff().dropna() >= 0).all()  # more capacity, more recall


def test_zero_positive_edge_case_is_reported(tmp_path):
    cfg = load("configs/base.yaml", set_seeds=False)
    n = 500
    y = np.zeros(n, dtype=int)
    y[-5:] = 1
    score = np.linspace(1, 0, n)  # positives get the LOWEST scores
    oof = pd.DataFrame({"fold": 0, "y_true": y, "score": score})
    res = TH.run_threshold(oof, cfg, n_cohort=885, tables_dir=tmp_path)
    assert res["zero_predicted_positives"] is True
