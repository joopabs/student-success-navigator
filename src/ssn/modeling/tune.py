"""Hyperparameter tuning under the same stratified CV (T048).

RandomizedSearchCV over the search space in configs/models/<name>.yaml, scoring = average
precision (PR-AUC), on the TRAINING split only. Each candidate is tuned in both selection settings
(all features vs the Milestone 4 embedded k=30 subset). Results and best parameters are written
so the Milestone 6 selection matrix can cite them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import loguniform, randint
from sklearn.model_selection import RandomizedSearchCV

from ssn.config import Config, load_model_config
from ssn.features.allowlist import Allowlist
from ssn.modeling.candidates import SelectionSetting, build_pipeline
from ssn.modeling.cv import make_cv

SCORING = {"pr_auc": "average_precision", "roc_auc": "roc_auc"}


def distribution(spec: dict[str, Any]):
    kind = spec["type"]
    if kind == "loguniform":
        return loguniform(spec["low"], spec["high"])
    if kind == "randint":
        return randint(int(spec["low"]), int(spec["high"]) + 1)
    if kind == "uniform":
        from scipy.stats import uniform

        return uniform(spec["low"], spec["high"] - spec["low"])
    if kind == "choice":
        return list(spec["values"])
    raise ValueError(f"unknown search-space type {kind!r}")


def search_space(name: str, cfg: Config) -> dict[str, Any]:
    mc = load_model_config(name, cfg)
    return {f"clf__{k}": distribution(v) for k, v in mc.search_space.items()}


def tune_one(
    name: str,
    X: pd.DataFrame,
    y: pd.Series,
    cfg: Config,
    allow: Allowlist,
    selection: SelectionSetting | None,
    *,
    n_iter: int | None = None,
    n_jobs: int = -1,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    mc = load_model_config(name, cfg)
    pipe = build_pipeline(name, cfg, allow, selection=selection)
    space = search_space(name, cfg)
    n = n_iter if n_iter is not None else int(mc.n_iter)
    search = RandomizedSearchCV(
        pipe,
        param_distributions=space,
        n_iter=n,
        scoring=SCORING,
        refit="pr_auc",
        cv=make_cv(cfg),
        random_state=cfg.seed,
        n_jobs=n_jobs,
        return_train_score=False,
    )
    search.fit(X, y)
    res = pd.DataFrame(search.cv_results_)
    keep = [c for c in res.columns if c.startswith("param_")] + [
        "mean_test_pr_auc",
        "std_test_pr_auc",
        "rank_test_pr_auc",
        "mean_test_roc_auc",
        "std_test_roc_auc",
        "mean_fit_time",
    ]
    table = res[keep].sort_values("rank_test_pr_auc").reset_index(drop=True)
    table.insert(0, "selection", "decided" if selection is not None else "none")
    table.insert(0, "model", name)
    best = {
        "model": name,
        "selection": "decided" if selection is not None else "none",
        "best_params": {
            k.replace("clf__", ""): (v.item() if hasattr(v, "item") else v)
            for k, v in search.best_params_.items()
        },
        "cv_pr_auc_mean": float(search.cv_results_["mean_test_pr_auc"][search.best_index_]),
        "cv_pr_auc_std": float(search.cv_results_["std_test_pr_auc"][search.best_index_]),
        "cv_roc_auc_mean": float(search.cv_results_["mean_test_roc_auc"][search.best_index_]),
        "n_iter": int(n),
        "n_folds": int(cfg.get("split.cv_folds")),
        "seed": cfg.seed,
    }
    return table, best


def run_tuning(
    X: pd.DataFrame,
    y: pd.Series,
    cfg: Config,
    allow: Allowlist,
    models: list[str],
    selection: SelectionSetting | None,
    tables_dir: Path,
    *,
    n_iter: int | None = None,
) -> dict[str, dict[str, Any]]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    tuned: dict[str, dict[str, Any]] = {}
    for name in models:
        if name == "dummy":
            continue
        mc = load_model_config(name, cfg)
        settings = [None, selection] if (mc.use_selection and selection is not None) else [None]
        frames = []
        for sel in settings:
            table, best = tune_one(name, X, y, cfg, allow, sel, n_iter=n_iter)
            frames.append(table)
            tuned[f"{name}__sel-{best['selection']}"] = best
        pd.concat(frames, ignore_index=True).to_csv(
            tables_dir / f"tuning_results_{name}.csv", index=False
        )
    (tables_dir / "tuned_params.json").write_text(json.dumps(tuned, indent=2, default=float) + "\n")
    return tuned


def load_tuned(tables_dir: Path) -> dict[str, dict[str, Any]]:
    return json.loads((tables_dir / "tuned_params.json").read_text())


def _clean(v):
    return v.item() if isinstance(v, np.generic) else v
