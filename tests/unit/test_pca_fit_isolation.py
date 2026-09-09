from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ssn.config import load
from ssn.features import allowlist as al
from ssn.features.preprocess import project_for_model
from ssn.modeling import pca as P


@pytest.fixture(scope="module")
def cfg():
    return load("configs/base.yaml", set_seeds=False)


@pytest.fixture(scope="module")
def allow():
    return al.load("configs/features.yaml")


def test_pca_components_unchanged_by_rows_outside_training_indices(real_named_frame, allow, cfg):
    X = project_for_model(real_named_frame, allow)
    y = real_named_frame["is_dropout"]
    idx = np.arange(0, 190)
    a = P.build_pca_pipeline(allow, 5, cfg.seed).fit(X.iloc[idx], y.iloc[idx])
    X_more = pd.concat([X, X.iloc[:30].assign(**{"Admission grade": 0.0})], ignore_index=True)
    y_more = pd.concat([y, y.iloc[:30]], ignore_index=True)
    b = P.build_pca_pipeline(allow, 5, cfg.seed).fit(X_more.iloc[idx], y_more.iloc[idx])
    np.testing.assert_allclose(
        a.named_steps["pca"].components_, b.named_steps["pca"].components_, atol=1e-10
    )
    np.testing.assert_allclose(
        a.named_steps["pca"].explained_variance_ratio_,
        b.named_steps["pca"].explained_variance_ratio_,
        atol=1e-10,
    )


def test_explained_variance_table_is_monotone_and_threshold_count(real_named_frame, allow, cfg):
    X = project_for_model(real_named_frame, allow)
    y = real_named_frame["is_dropout"]
    table, scores2d = P.explained_variance(X, y, allow, cfg)
    assert scores2d.shape == (len(X), 2)
    assert (np.diff(table["cumulative"]) >= -1e-12).all()
    assert abs(table["cumulative"].iloc[-1] - 1.0) < 1e-6
    n = P.n_components_for(table, 0.95)
    assert 1 <= n <= len(table) and table.loc[n - 1, "cumulative"] >= 0.95


def test_run_pca_writes_all_outputs(real_named_frame, allow, cfg, tmp_path, monkeypatch):
    X = project_for_model(real_named_frame, allow)
    y = real_named_frame["is_dropout"]
    monkeypatch.setitem(cfg.raw["pca"], "compare_in_cv", True)
    out = P.run_pca(X, y, cfg, allow, tmp_path / "tables", tmp_path / "figures")
    assert set(out) == {"explained_variance", "compare", "scree", "projection"}
    assert all(p.exists() for p in out.values())
    cmp = pd.read_csv(out["compare"])
    assert set(cmp["pipeline"]) >= {"no_pca", "pca_2_components"}
    assert (cmp["n_components_at_threshold"] >= 1).all()


def test_pca_command_reads_only_train(monkeypatch, tmp_path, real_named_frame, cfg):
    from ssn.modeling import commands as MC

    seen = []
    real = pd.read_parquet
    monkeypatch.setattr(
        pd, "read_parquet", lambda p, *a, **k: (seen.append(str(p)), real(p, *a, **k))[1]
    )
    proc = tmp_path / "processed"
    proc.mkdir()
    real_named_frame.to_parquet(proc / "train.parquet", index=False)
    real_named_frame.to_parquet(proc / "test.parquet", index=False)
    monkeypatch.setattr(
        cfg.__class__,
        "path_for",
        lambda self, key: proc if key == "processed_dir" else cfg.root / "reports",
    )
    MC.load_train(cfg, al.load("configs/features.yaml"))
    assert all("test.parquet" not in p for p in seen)
