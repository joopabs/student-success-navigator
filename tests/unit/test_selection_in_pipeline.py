from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ssn.config import load
from ssn.features import allowlist as al
from ssn.features.preprocess import project_for_model
from ssn.modeling import cv as CV
from ssn.modeling import selection as SEL


@pytest.fixture(scope="module")
def cfg():
    return load("configs/base.yaml", set_seeds=False)


@pytest.fixture(scope="module")
def allow():
    return al.load("configs/features.yaml")


def _xy(real_named_frame, allow):
    X = project_for_model(real_named_frame, allow)
    y = real_named_frame["is_dropout"]
    return X, y


@pytest.mark.parametrize(
    "k,n_fold,n_test,expected",
    [(50, 177, 885, 10), (50, 708, 885, 40), (1, 10, 885, 1), (50, 885, 885, 50)],
)
def test_k_for_fold_scales_selection_rate(k, n_fold, n_test, expected):
    assert CV.k_for_fold(k, n_fold, n_test) == expected


def test_k_for_fold_rejects_bad_cohort_size():
    with pytest.raises(ValueError):
        CV.k_for_fold(50, 100, 0)


def test_oof_covers_every_row_once(real_named_frame, allow, cfg):
    X, y = _xy(real_named_frame, allow)
    pipe = SEL.build_selection_pipeline(allow, "filter", "anova_f", 10, cfg.seed)
    res = CV.oof_predict(pipe, X, y, CV.make_cv(cfg))
    assert len(res.scores) == len(X) and not np.isnan(res.scores).any()
    assert sorted(set(res.folds)) == list(range(cfg.get("split.cv_folds")))
    assert ((res.scores >= 0) & (res.scores <= 1)).all()


@pytest.mark.parametrize(
    "kind,method",
    [
        ("filter", "mutual_info"),
        ("filter", "anova_f"),
        ("embedded", "l1_logreg"),
        ("embedded", "tree_importance"),
    ],
)
def test_selector_is_a_pipeline_step_and_selects_k(real_named_frame, allow, cfg, kind, method):
    X, y = _xy(real_named_frame, allow)
    pipe = SEL.build_selection_pipeline(allow, kind, method, 12, cfg.seed)
    assert [name for name, _ in pipe.steps] == ["pre", "select", "clf"]
    pipe.fit(X, y)
    assert int(pipe.named_steps["select"].get_support().sum()) == 12


def test_selector_fit_ignores_rows_outside_training_indices(real_named_frame, allow, cfg):
    """Fitting on train indices yields the same support regardless of extra rows in the frame."""
    X, y = _xy(real_named_frame, allow)
    train_idx = np.arange(0, 180)
    pipe_a = SEL.build_selection_pipeline(allow, "embedded", "l1_logreg", 15, cfg.seed).fit(
        X.iloc[train_idx], y.iloc[train_idx]
    )
    X_more = pd.concat([X, X.iloc[:40].assign(**{"Admission grade": 199.0})], ignore_index=True)
    y_more = pd.concat([y, 1 - y.iloc[:40]], ignore_index=True)
    pipe_b = SEL.build_selection_pipeline(allow, "embedded", "l1_logreg", 15, cfg.seed).fit(
        X_more.iloc[train_idx], y_more.iloc[train_idx]
    )
    np.testing.assert_array_equal(
        pipe_a.named_steps["select"].get_support(), pipe_b.named_steps["select"].get_support()
    )


def test_decide_applies_parsimony_rule(cfg):
    table = pd.DataFrame(
        [
            {
                "kind": "filter",
                "method": "mutual_info",
                "k": 10,
                "pr_auc_mean": 0.70,
                "pr_auc_std": 0.01,
            },
            {
                "kind": "filter",
                "method": "mutual_info",
                "k": 20,
                "pr_auc_mean": 0.79,
                "pr_auc_std": 0.01,
            },
            {
                "kind": "embedded",
                "method": "l1_logreg",
                "k": 20,
                "pr_auc_mean": 0.795,
                "pr_auc_std": 0.01,
            },
            {
                "kind": "embedded",
                "method": "l1_logreg",
                "k": "all",
                "pr_auc_mean": 0.80,
                "pr_auc_std": 0.01,
            },
        ]
    )
    d = SEL.decide(table, cfg, n_features=100)
    assert d.k == 20 and d.kind == "filter"  # smallest k within 1 std of best; filter wins the tie
    assert d.best_pr_auc_mean == 0.8 and "Not a model-performance claim" in d.note


def test_cv_by_k_and_describe_outputs_have_expected_shape(
    real_named_frame, allow, cfg, monkeypatch
):
    X, y = _xy(real_named_frame, allow)
    monkeypatch.setitem(cfg.raw["selection"], "k_grid", [5, "all"])
    methods = {"filter": ("anova_f", "SelectKBest"), "embedded": ("l1_logreg", "SelectFromModel")}
    table = SEL.cv_by_k(X, y, cfg, allow, methods)
    assert len(table) == 4 and {"kind", "method", "k", "pr_auc_mean", "pr_auc_std"} <= set(
        table.columns
    )
    scores = SEL.describe_scores(X, y, cfg, allow, methods)
    assert set(scores) == {"filter", "embedded"}
    for tbl in scores.values():
        assert {"feature", "score", "source_column"} <= set(tbl.columns)
        assert tbl["selected_frequency_top20"].between(0, 1).all()


def test_select_command_reads_only_train(monkeypatch, tmp_path, real_named_frame, cfg):
    """The select handler must never open test.parquet."""
    from ssn.modeling import commands as MC

    seen = []
    real = pd.read_parquet

    def spy(path, *a, **k):
        seen.append(str(path))
        return real(path, *a, **k)

    monkeypatch.setattr(pd, "read_parquet", spy)
    proc = tmp_path / "processed"
    proc.mkdir()
    real_named_frame.to_parquet(proc / "train.parquet", index=False)
    real_named_frame.to_parquet(proc / "test.parquet", index=False)
    monkeypatch.setattr(
        cfg.__class__,
        "path_for",
        lambda self, key: proc if key == "processed_dir" else cfg.root / "reports",
    )
    allow = al.load("configs/features.yaml")
    _, X, y = MC.load_train(cfg, allow)
    assert len(X) == len(real_named_frame)
    assert all("test.parquet" not in p for p in seen) and any("train.parquet" in p for p in seen)
