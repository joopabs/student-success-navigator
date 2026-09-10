from __future__ import annotations

import pytest

from ssn.config import load
from ssn.features import allowlist as al
from ssn.features.preprocess import project_for_model
from ssn.modeling import tune as TU
from ssn.modeling.candidates import SelectionSetting


def test_search_space_builds_distributions():
    cfg = load("configs/base.yaml", set_seeds=False)
    space = TU.search_space("hist_gb", cfg)
    assert set(space) == {
        "clf__learning_rate",
        "clf__max_leaf_nodes",
        "clf__min_samples_leaf",
        "clf__l2_regularization",
    }
    assert hasattr(space["clf__learning_rate"], "rvs")
    assert TU.search_space("dummy", cfg) == {}


@pytest.mark.parametrize("name", ["logreg", "hist_gb"])
def test_tune_one_small_budget_on_fixture(real_named_frame, name, monkeypatch):
    cfg = load("configs/base.yaml", set_seeds=False)
    monkeypatch.setitem(cfg.raw["split"], "cv_folds", 3)
    allow = al.load("configs/features.yaml")
    X = project_for_model(real_named_frame, allow)
    y = real_named_frame["is_dropout"]
    table, best = TU.tune_one(name, X, y, cfg, allow, None, n_iter=2, n_jobs=1)
    assert len(table) == 2 and best["n_iter"] == 2 and best["seed"] == cfg.seed
    assert 0 <= best["cv_pr_auc_mean"] <= 1 and set(best["best_params"])
    assert list(table["model"].unique()) == [name] and (table["selection"] == "none").all()


def test_run_tuning_writes_tables_and_params(real_named_frame, tmp_path, monkeypatch):
    cfg = load("configs/base.yaml", set_seeds=False)
    monkeypatch.setitem(cfg.raw["split"], "cv_folds", 3)
    allow = al.load("configs/features.yaml")
    X = project_for_model(real_named_frame, allow)
    y = real_named_frame["is_dropout"]
    tuned = TU.run_tuning(
        X,
        y,
        cfg,
        allow,
        ["dummy", "logreg"],
        SelectionSetting("embedded", "l1_logreg", 8),
        tmp_path,
        n_iter=2,
    )
    assert set(tuned) == {"logreg__sel-none", "logreg__sel-decided"}
    assert (tmp_path / "tuning_results_logreg.csv").exists() and (
        tmp_path / "tuned_params.json"
    ).exists()
    assert TU.load_tuned(tmp_path) == tuned
