"""Train-only feature selection as scikit-learn pipeline steps (T037).

Filter: SelectKBest with mutual information (or ANOVA F). Embedded: SelectFromModel wrapping an
L1 logistic regression (or a random-forest importance ranking). Both are pipeline steps, so under
`cross_validate` they are fitted on the training folds only. Scores reported for the full training
split are for description; the method/k decision comes from the CV table.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectFromModel, SelectKBest, f_classif, mutual_info_classif
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_validate
from sklearn.pipeline import Pipeline

from ssn.config import Config
from ssn.features.allowlist import Allowlist
from ssn.features.preprocess import build_preprocessor
from ssn.modeling.cv import make_cv

SCORING = {"pr_auc": "average_precision", "roc_auc": "roc_auc"}


def make_filter(method: str, k: int | str, seed: int) -> SelectKBest:
    if method == "mutual_info":

        def mi(X, y):
            return mutual_info_classif(X, y, random_state=seed)

        return SelectKBest(score_func=mi, k=k)
    if method == "anova_f":
        return SelectKBest(score_func=f_classif, k=k)
    raise ValueError(f"unknown filter method {method!r}")


def make_embedded(method: str, k: int | str, seed: int) -> SelectFromModel:
    max_features = None if k == "all" else int(k)
    if method == "l1_logreg":
        est = LogisticRegression(
            l1_ratio=1.0,
            solver="liblinear",
            C=0.5,
            class_weight="balanced",
            random_state=seed,
            max_iter=2000,
        )  # l1_ratio=1.0 == L1 penalty (sklearn >= 1.8 API)
        return SelectFromModel(est, max_features=max_features, threshold=-np.inf)
    if method == "tree_importance":
        est = RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced_subsample",
            random_state=seed,
            n_jobs=1,
            min_samples_leaf=5,
        )
        return SelectFromModel(est, max_features=max_features, threshold=-np.inf)
    raise ValueError(f"unknown embedded method {method!r}")


def reference_estimator(seed: int) -> LogisticRegression:
    return LogisticRegression(class_weight="balanced", max_iter=3000, random_state=seed)


def build_selection_pipeline(
    allow: Allowlist, kind: str, method: str, k: int | str, seed: int
) -> Pipeline:
    """preprocess -> selector -> reference logistic regression."""
    pre = build_preprocessor(allow)
    selector = make_filter(method, k, seed) if kind == "filter" else make_embedded(method, k, seed)
    return Pipeline([("pre", pre), ("select", selector), ("clf", reference_estimator(seed))])


@dataclass
class SelectionDecision:
    kind: str
    method: str
    k: int | str
    cv_pr_auc_mean: float
    cv_pr_auc_std: float
    best_pr_auc_mean: float
    rule: str
    n_transformed_features: int
    note: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def cv_by_k(
    X: pd.DataFrame,
    y: pd.Series,
    cfg: Config,
    allow: Allowlist,
    methods: dict[str, tuple[str, str]],
) -> pd.DataFrame:
    """CV PR-AUC/ROC-AUC for each (kind, method) x k in the grid. Fitting happens inside folds."""
    cv = make_cv(cfg)
    rows = []
    for kind, (method, _) in methods.items():
        for k in cfg.get("selection.k_grid"):
            pipe = build_selection_pipeline(allow, kind, method, k, cfg.seed)
            res = cross_validate(
                pipe, X, y, cv=cv, scoring=SCORING, n_jobs=1, return_train_score=False
            )
            rows.append(
                {
                    "kind": kind,
                    "method": method,
                    "k": k,
                    "pr_auc_mean": float(np.mean(res["test_pr_auc"])),
                    "pr_auc_std": float(np.std(res["test_pr_auc"], ddof=1)),
                    "roc_auc_mean": float(np.mean(res["test_roc_auc"])),
                    "roc_auc_std": float(np.std(res["test_roc_auc"], ddof=1)),
                    "fit_time_s": float(np.mean(res["fit_time"])),
                }
            )
    return pd.DataFrame(rows)


def decide(table: pd.DataFrame, cfg: Config, n_features: int) -> SelectionDecision:
    """Parsimony rule: among settings within `parsimony_std_rule` CV std of the best mean PR-AUC,
    choose the smallest k (ties -> filter before embedded, for speed and transparency)."""
    std_rule = float(cfg.get("selection.parsimony_std_rule"))
    best = table.loc[table["pr_auc_mean"].idxmax()]
    threshold = best["pr_auc_mean"] - std_rule * best["pr_auc_std"]
    eligible = table[table["pr_auc_mean"] >= threshold].copy()
    eligible["k_num"] = eligible["k"].apply(lambda v: n_features if v == "all" else int(v))
    eligible["kind_rank"] = eligible["kind"].map({"filter": 0, "embedded": 1})
    pick = eligible.sort_values(
        ["k_num", "kind_rank", "pr_auc_mean"], ascending=[True, True, False]
    ).iloc[0]
    return SelectionDecision(
        kind=str(pick["kind"]),
        method=str(pick["method"]),
        k=pick["k"] if pick["k"] == "all" else int(pick["k"]),
        cv_pr_auc_mean=round(float(pick["pr_auc_mean"]), 4),
        cv_pr_auc_std=round(float(pick["pr_auc_std"]), 4),
        best_pr_auc_mean=round(float(best["pr_auc_mean"]), 4),
        rule=(
            f"smallest k with mean PR-AUC >= best - {std_rule} x std(best) under "
            f"{int(cfg.get('split.cv_folds'))}-fold stratified CV on the training split, "
            "reference estimator = class-weighted logistic regression"
        ),
        n_transformed_features=int(n_features),
        note=(
            "Selection setting for downstream candidate pipelines (Milestone 5). "
            "Not a model-performance claim."
        ),
    )


def _feature_names(pre: Pipeline) -> list[str]:
    return list(pre.named_steps["columns"].get_feature_names_out())


def describe_scores(
    X: pd.DataFrame,
    y: pd.Series,
    cfg: Config,
    allow: Allowlist,
    methods: dict[str, tuple[str, str]],
) -> dict[str, pd.DataFrame]:
    """Descriptive rankings on the full TRAINING split plus per-fold selection frequency."""
    cv = make_cv(cfg)
    out: dict[str, pd.DataFrame] = {}
    for kind, (method, _) in methods.items():
        pre = build_preprocessor(allow).fit(X, y)  # training split only
        Xt = pre.transform(X)
        names = _feature_names(pre)
        sel_all = (
            make_filter(method, "all", cfg.seed)
            if kind == "filter"
            else make_embedded(method, "all", cfg.seed)
        )
        sel_all.fit(Xt, y)
        if kind == "filter":
            score = sel_all.scores_
        else:
            est = sel_all.estimator_
            score = np.abs(est.coef_.ravel()) if hasattr(est, "coef_") else est.feature_importances_
        freq = np.zeros(len(names))
        k_freq = 20
        for tr, _va in cv.split(X, y):
            pre_f = build_preprocessor(allow).fit(X.iloc[tr], y.iloc[tr])
            sel = (
                make_filter(method, k_freq, cfg.seed)
                if kind == "filter"
                else make_embedded(method, k_freq, cfg.seed)
            )
            sel.fit(pre_f.transform(X.iloc[tr]), y.iloc[tr])
            names_f = _feature_names(pre_f)
            chosen = {names_f[i] for i in np.flatnonzero(sel.get_support())}
            freq += np.array([n in chosen for n in names])
        table = pd.DataFrame(
            {
                "feature": names,
                "score": score,
                f"selected_frequency_top{k_freq}": freq / cv.get_n_splits(),
            }
        )
        table["source_column"] = (
            table["feature"].str.split("__").str[1].str.replace(r"_\d+(\.\d+)?$", "", regex=True)
        )
        out[kind] = table.sort_values("score", ascending=False).reset_index(drop=True)
    return out


def write_outputs(
    tables_dir: Path,
    cv_table: pd.DataFrame,
    scores: dict[str, pd.DataFrame],
    decision: SelectionDecision,
) -> list[Path]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    written = []
    p = tables_dir / "selection_cv_by_k.csv"
    cv_table.to_csv(p, index=False)
    written.append(p)
    for kind, tbl in scores.items():
        p = tables_dir / f"selection_{kind}_scores.csv"
        tbl.to_csv(p, index=False)
        written.append(p)
    p = tables_dir / "selection_decision.json"
    p.write_text(decision.to_json() + "\n")
    written.append(p)
    return written


def configured_methods(cfg: Config) -> dict[str, tuple[str, str]]:
    return {
        "filter": (str(cfg.get("selection.filter_method")), "SelectKBest"),
        "embedded": (str(cfg.get("selection.embedded_method")), "SelectFromModel"),
    }


def load_decision(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())
