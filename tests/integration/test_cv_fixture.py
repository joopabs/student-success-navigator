from __future__ import annotations

import pandas as pd
import pytest

from ssn.config import load
from ssn.features import allowlist as al
from ssn.modeling import traincv as TC


@pytest.fixture(scope="module")
def cfg():
    return load("configs/base.yaml", set_seeds=False)


@pytest.fixture(scope="module")
def allow():
    return al.load("configs/features.yaml")


@pytest.fixture(scope="module")
def train(real_named_frame):
    df = real_named_frame.copy()
    df.insert(0, "record_id", [f"R{i:08x}" for i in range(len(df))])
    return df


def test_variants_enumerate_dummy_and_expected_combinations(cfg):
    sel = TC.SelectionSetting("embedded", "l1_logreg", 12)
    vs = TC.variants_for(["dummy", "logreg", "hist_gb"], cfg, sel)
    keys = {v.key for v in vs}
    assert "dummy__sel-none__imb-none" in keys
    assert (
        "logreg__sel-decided__imb-smotenc" in keys and "logreg__sel-none__imb-class_weight" in keys
    )
    assert not any(k.startswith("hist_gb") and "smotenc" in k for k in keys)


def test_run_train_cv_on_fixture(train, cfg, allow, tmp_path, monkeypatch):
    monkeypatch.setitem(cfg.raw["imbalance"], "compare_smote", True)
    monkeypatch.setitem(cfg.raw["split"], "cv_folds", 3)
    seen = []
    real = pd.read_parquet
    monkeypatch.setattr(
        pd, "read_parquet", lambda p, *a, **k: (seen.append(str(p)), real(p, *a, **k))[1]
    )
    table, oofs = TC.run_train_cv(train, cfg, allow, ["logreg"], write=False)
    assert set(table["model"]) == {"dummy", "logreg"}
    assert {
        "variant",
        "seed",
        "n_folds",
        "fit_time_s_mean",
        "pr_auc_mean",
        "pr_auc_std",
        "roc_auc_mean",
        "recall_at_k_mean",
        "precision_at_k_mean",
        "brier_mean",
        "ece_mean",
        "accuracy_at_threshold_mean",
        "f1_at_threshold_mean",
        "topk_tp_sum",
        "thr_tp_sum",
        "capacity_k",
        "n_cohort_expected",
    } <= set(table.columns)
    assert (table["n_folds"] == 3).all() and (table["seed"] == cfg.seed).all()
    for key, oof in oofs.items():
        assert len(oof) == len(train) and not oof["score"].isna().any(), key
        assert sorted(oof["fold"].unique()) == [0, 1, 2]
        assert (oof["record_id"].to_numpy() == train["record_id"].to_numpy()).all()
    assert all("test.parquet" not in p for p in seen)


def test_smote_does_not_change_validation_fold_sizes(train, cfg, allow, monkeypatch):
    """One OOF score per ORIGINAL row: resampling affects training folds only."""
    monkeypatch.setitem(cfg.raw["split"], "cv_folds", 3)
    sel = None
    v = TC.Variant("logreg", "none", "smotenc")
    from ssn.features.preprocess import project_for_model

    X = project_for_model(train, allow)
    y = train["is_dropout"]
    row, oof = TC.run_variant(v, X, y, cfg, allow, sel, n_cohort=885)
    assert len(oof) == len(X) and oof["fold"].value_counts().sum() == len(X)
    assert row["n_train"] == len(X)


def test_ablation_promotes_columns_for_analysis_only(train, cfg, allow, monkeypatch):
    monkeypatch.setitem(cfg.raw["split"], "cv_folds", 3)
    promoted = TC.promoted_allowlist(cfg, "ambiguous")
    assert (
        promoted.ambiguous == frozenset()
        and len(promoted.allowed_source) == len(allow.allowed_source) + 3
    )
    sens = TC.promoted_allowlist(cfg, "sensitive")
    assert (
        sens.sensitive == frozenset() and len(sens.allowed_source) == len(allow.allowed_source) + 6
    )
    # the real allow-list on disk is untouched
    assert al.load("configs/features.yaml").ambiguous == allow.ambiguous


def test_expected_cohort_size_reads_split_summary(cfg):
    assert TC.expected_cohort_size(cfg) == 885
