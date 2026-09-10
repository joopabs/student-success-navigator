from __future__ import annotations

import json

import pandas as pd

from ssn.config import load
from ssn.features import allowlist as al
from ssn.modeling import reproduce as RP
from ssn.modeling import traincv as TC


def _run(train, cfg, allow, out_dir):
    table, _ = TC.run_train_cv(train, cfg, allow, ["logreg"], write=False)
    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(out_dir / "cv_comparison.csv", index=False)
    (out_dir / "threshold_and_bands.json").write_text(
        json.dumps({"threshold": float(table["pr_auc_mean"].iloc[-1]), "bands": [{"lower": 0.5}]})
    )
    return table


def test_two_seeded_fixture_runs_are_identical(tmp_path, real_named_frame, monkeypatch):
    cfg = load("configs/base.yaml", set_seeds=False)
    monkeypatch.setitem(cfg.raw["split"], "cv_folds", 3)
    monkeypatch.setitem(cfg.raw["imbalance"], "compare_smote", False)
    allow = al.load("configs/features.yaml")
    train = real_named_frame.copy()
    train.insert(0, "record_id", [f"R{i:08x}" for i in range(len(train))])
    a = _run(train, cfg, allow, tmp_path / "a")
    b = _run(train, cfg, allow, tmp_path / "b")
    time_cols = [c for c in a.columns if "time" in c]
    pd.testing.assert_frame_equal(a.drop(columns=time_cols), b.drop(columns=time_cols))
    deltas = RP.compare_runs(tmp_path / "a", tmp_path / "b")
    assert len(deltas) > 0 and (deltas["max_abs_delta"] == 0).all()
    ok = RP.write_report(deltas, 1e-9, tmp_path / "REPRODUCIBILITY.md", "a", "b")
    assert ok and "PASS" in (tmp_path / "REPRODUCIBILITY.md").read_text()


def test_perturbed_run_is_detected(tmp_path, real_named_frame, monkeypatch):
    cfg = load("configs/base.yaml", set_seeds=False)
    monkeypatch.setitem(cfg.raw["split"], "cv_folds", 3)
    monkeypatch.setitem(cfg.raw["imbalance"], "compare_smote", False)
    allow = al.load("configs/features.yaml")
    train = real_named_frame.copy()
    train.insert(0, "record_id", [f"R{i:08x}" for i in range(len(train))])
    _run(train, cfg, allow, tmp_path / "a")
    t = pd.read_csv(tmp_path / "a" / "cv_comparison.csv")
    (tmp_path / "b").mkdir()
    t.assign(pr_auc_mean=t["pr_auc_mean"] + 0.02).to_csv(
        tmp_path / "b" / "cv_comparison.csv", index=False
    )
    deltas = RP.compare_runs(tmp_path / "a", tmp_path / "b")
    assert deltas.loc[deltas["column"] == "pr_auc_mean", "max_abs_delta"].iloc[0] > 0.019
    assert not RP.write_report(deltas, 0.005, tmp_path / "R.md", "a", "b")
