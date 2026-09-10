from __future__ import annotations

import numpy as np
import pandas as pd

from ssn.app.services import prioritization as P

BANDS = [
    {"name": "top", "lower": 0.7, "upper": 1.0},
    {"name": "mid", "lower": 0.5, "upper": 0.7},
    {"name": "rest", "lower": 0.0, "upper": 0.5},
]


def test_rank_orders_by_score_then_record_id():
    ids = pd.Series(["Rc", "Ra", "Rb", "Rd"])
    ranked = P.rank_cohort(ids, np.array([0.9, 0.9, 0.2, 0.6]), BANDS)
    assert list(ranked["record_id"]) == ["Ra", "Rc", "Rd", "Rb"]  # tie 0.9 broken by id asc
    assert list(ranked["rank"]) == [1, 2, 3, 4]
    assert list(ranked["band"]) == ["top", "top", "mid", "rest"]


def test_top_k_exact_and_notice_when_k_exceeds_cohort():
    ranked = P.rank_cohort(pd.Series([f"R{i}" for i in range(5)]), np.linspace(1, 0, 5), BANDS)
    rows, notice = P.top_k(ranked, 3)
    assert len(rows) == 3 and notice is None
    rows, notice = P.top_k(ranked, 9)
    assert len(rows) == 5 and "exceeds the cohort size" in notice


def test_bands_come_from_manifest_not_recomputed(fixture_state):
    st = fixture_state
    for _, r in st.ranked.head(20).iterrows():
        expected = next(b["name"] for b in st.bundle.bands if r["score"] >= b["lower"])
        assert r["band"] == expected


def test_k_options_derive_from_config(fixture_state):
    st = fixture_state
    assert st.k_options == [
        st.per_week * w for w in st.cfg.get("capacity.window_sensitivity_weeks")
    ]
    assert st.k_default in st.k_options
