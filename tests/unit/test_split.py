from __future__ import annotations

import pandas as pd
import pytest

from ssn.config import load
from ssn.data import split as SP
from ssn.features import allowlist as al


@pytest.fixture()
def cfg():
    return load("configs/base.yaml", set_seeds=False)


def _fixture_with_age(synthetic_frame):
    df = synthetic_frame.copy()
    df["Age at enrollment"] = df["sens_age"]
    return df


def test_demo_cohort_has_no_labels_or_sensitive_columns(synthetic_frame, features_yaml, cfg):
    allow = al.load(features_yaml)
    out = SP.make_split(synthetic_frame, cfg, allow)
    forbidden = {"Target", "is_dropout", "age_band", "sem2_approved", "fin_status_flag"} | set(
        allow.sensitive
    )
    assert not forbidden & set(out.demo.columns)
    assert set(out.demo.columns) == {"record_id"} | allow.allowed_source


def test_evaluator_file_carries_labels_and_sensitive_columns_only(
    synthetic_frame, features_yaml, cfg
):
    allow = al.load(features_yaml)
    out = SP.make_split(synthetic_frame, cfg, allow)
    assert (
        set(out.evaluation.columns)
        == {"record_id", "is_dropout", "Target", "age_band"} | allow.sensitive
    )
    assert not allow.allowed_source & set(out.evaluation.columns)


def test_train_test_disjoint_and_ids_unique(synthetic_frame, features_yaml, cfg):
    out = SP.make_split(synthetic_frame, cfg, al.load(features_yaml))
    assert not set(out.train["record_id"]) & set(out.test["record_id"])
    ids = pd.concat([out.train["record_id"], out.test["record_id"]])
    assert ids.is_unique and len(ids) == len(synthetic_frame)
    assert (
        set(out.demo["record_id"]) == set(out.evaluation["record_id"]) == set(out.test["record_id"])
    )


def test_synthetic_id_is_not_row_index(synthetic_frame, features_yaml, cfg):
    out = SP.make_split(synthetic_frame, cfg, al.load(features_yaml))
    assert out.train["record_id"].str.match(r"^R[0-9a-f]{8}$").all()
    # ids should not be monotone in row order
    ordered = list(pd.concat([out.train, out.test]).sort_index()["record_id"])
    assert ordered != sorted(ordered)


def test_is_dropout_mapping_and_stratification(synthetic_frame, features_yaml, cfg):
    out = SP.make_split(synthetic_frame, cfg, al.load(features_yaml))
    full = pd.concat([out.train, out.test])
    assert ((full["Target"] == "Dropout").astype(int) == full["is_dropout"]).all()
    overall = synthetic_frame["Target"].eq("Dropout").mean()
    assert abs(out.train["is_dropout"].mean() - overall) < 0.08
    assert abs(out.test["is_dropout"].mean() - overall) < 0.12
    assert abs(len(out.test) / len(synthetic_frame) - cfg.get("split.test_size")) < 0.05


def test_split_is_deterministic(synthetic_frame, features_yaml, cfg):
    a = SP.make_split(synthetic_frame, cfg, al.load(features_yaml))
    b = SP.make_split(synthetic_frame, cfg, al.load(features_yaml))
    pd.testing.assert_frame_equal(a.train, b.train)
    pd.testing.assert_frame_equal(a.demo, b.demo)


def test_age_band_applied_when_age_column_present(synthetic_frame, features_yaml, cfg):
    df = _fixture_with_age(synthetic_frame)
    out = SP.make_split(df, cfg, al.load(features_yaml))
    bands = {b["name"] for b in cfg.get("fairness.age_bands")}
    assert set(out.evaluation["age_band"].dropna()) <= bands
    assert out.evaluation["age_band"].notna().all()
