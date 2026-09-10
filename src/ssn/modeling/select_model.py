"""Multi-criteria model selection (T050, constitution Principle VIII).

For every tuned candidate (model x selection setting) this computes out-of-fold metrics on the
TRAINING split with the tuned parameters, a preliminary fairness summary at the capacity
threshold, an explainability-feasibility flag, and maintainability facts. Accuracy is deliberately
absent from the matrix. The decision rule is lexicographic with a tolerance band and is written
into the decision file so it can be audited.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from ssn.config import Config
from ssn.fairness import metrics as FM
from ssn.fairness.groups import group_frame
from ssn.features.allowlist import Allowlist
from ssn.features.preprocess import project_for_model
from ssn.modeling import evaluate as EV
from ssn.modeling.candidates import SelectionSetting, build_pipeline
from ssn.modeling.cv import make_cv, oof_predict
from ssn.modeling.threshold import capacity_threshold, k_for_cohort
from ssn.modeling.traincv import expected_cohort_size, load_selection_setting

IS_DROPOUT = "is_dropout"
RECORD_ID = "record_id"
EXPLAINER = {
    "logreg": "shap.LinearExplainer (coefficients on named features)",
    "random_forest": "shap.TreeExplainer",
    "hist_gb": "shap.TreeExplainer",
}
MAINTAINABILITY = {
    "logreg": "linear; smallest artifact; coefficients readable; needs scaling (in pipeline)",
    "random_forest": "500 trees; largest artifact; robust to scaling; slower to fit and explain",
    "hist_gb": "boosted trees; compact; early stopping; sensitive to learning-rate/leaf settings",
}


def tuned_pipeline(
    key: str,
    tuned: dict[str, Any],
    cfg: Config,
    allow: Allowlist,
    selection: SelectionSetting | None,
):
    entry = tuned[key]
    sel = selection if entry["selection"] == "decided" else None
    return build_pipeline(
        entry["model"], cfg, allow, selection=sel, params_override=entry["best_params"]
    )


def evaluate_candidate(
    key: str,
    tuned: dict[str, Any],
    train: pd.DataFrame,
    cfg: Config,
    allow: Allowlist,
    selection: SelectionSetting | None,
    n_cohort: int,
) -> tuple[dict[str, Any], pd.DataFrame, Any]:
    X = project_for_model(train, allow)
    y = train[IS_DROPOUT].astype(int)
    pipe = tuned_pipeline(key, tuned, cfg, allow, selection)
    t0 = time.perf_counter()
    oof = oof_predict(pipe, X, y, make_cv(cfg))
    oof_time = time.perf_counter() - t0
    K = int(cfg.get("capacity.k"))
    k_train = k_for_cohort(K, len(X), n_cohort)
    thr = capacity_threshold(oof.scores, k_train)
    pred = (oof.scores >= thr).astype(int)
    groups = group_frame(train, cfg, allow)
    _, summary = FM.audit(oof.y, oof.scores, pred, groups, int(cfg.get("fairness.min_group_size")))
    entry = tuned[key]
    row = {
        "candidate": key,
        "model": entry["model"],
        "selection": entry["selection"],
        "best_params": json.dumps(entry["best_params"], default=str),
        "pr_auc": EV.pr_auc(oof.y, oof.scores),
        "pr_auc_std_cv": float(entry["cv_pr_auc_std"]),
        "roc_auc": EV.roc_auc(oof.y, oof.scores),
        "recall_at_k": EV.recall_at_k(oof.y, oof.scores, k_train),
        "precision_at_k": EV.precision_at_k(oof.y, oof.scores, k_train),
        "k_train": int(k_train),
        "brier": EV.brier(oof.y, oof.scores),
        "ece": EV.expected_calibration_error(oof.y, oof.scores),
        "fairness_max_dp_difference": float(summary["dp_difference"].max()),
        "fairness_min_di_ratio": float(summary["di_ratio"].min()),
        "fairness_max_eo_difference": float(summary["eo_difference"].max()),
        "explainability": EXPLAINER[entry["model"]],
        "explainability_native_shap": True,
        "maintainability": MAINTAINABILITY[entry["model"]],
        "oof_fit_time_s_total": float(oof_time),
        "seed": cfg.seed,
        "n_folds": int(cfg.get("split.cv_folds")),
    }
    frame = oof.frame(train[RECORD_ID] if RECORD_ID in train.columns else None)
    return row, frame, pipe


RULE = (
    "1) eligible = candidates whose OOF PR-AUC >= best PR-AUC - 1 x CV std of the best; "
    "2) rank eligible by Recall@K (rounded to 3 dp, desc), then ECE (2 dp, asc), "
    "then fairness_max_dp_difference (2 dp, asc), then Brier (3 dp, asc), then OOF fit time (asc). "
    "Accuracy is not a criterion (constitution VIII). "
    "Explainability must be natively SHAP-supported."
)


def decide(matrix: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    m = matrix[matrix["explainability_native_shap"]].copy()
    best = m.loc[m["pr_auc"].idxmax()]
    floor = best["pr_auc"] - best["pr_auc_std_cv"]
    eligible = m[m["pr_auc"] >= floor].copy()
    eligible["r_recall"] = eligible["recall_at_k"].round(3)
    eligible["r_ece"] = eligible["ece"].round(2)
    eligible["r_dp"] = eligible["fairness_max_dp_difference"].round(2)
    eligible["r_brier"] = eligible["brier"].round(3)
    ranked = eligible.sort_values(
        ["r_recall", "r_ece", "r_dp", "r_brier", "oof_fit_time_s_total"],
        ascending=[False, True, True, True, True],
    )
    ranked.insert(0, "rank", range(1, len(ranked) + 1))
    return str(ranked.iloc[0]["candidate"]), ranked


def run_select_model(
    train: pd.DataFrame,
    cfg: Config,
    allow: Allowlist,
    tuned: dict[str, Any],
    tables_dir: Path,
    processed_dir: Path,
    candidates_dir: Path,
) -> dict[str, Any]:
    selection = load_selection_setting(cfg)
    n_cohort = expected_cohort_size(cfg)
    rows, pipes = [], {}
    for key in tuned:
        row, oof_frame, pipe = evaluate_candidate(
            key, tuned, train, cfg, allow, selection, n_cohort
        )
        rows.append(row)
        oof_frame.to_parquet(processed_dir / f"oof_tuned_{key}.parquet", index=False)
        pipes[key] = pipe
    matrix = pd.DataFrame(rows).sort_values("pr_auc", ascending=False).reset_index(drop=True)
    assert "accuracy" not in " ".join(matrix.columns)
    chosen, ranked = decide(matrix)
    tables_dir.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(tables_dir / "selection_matrix.csv", index=False)
    ranked.to_csv(tables_dir / "selection_matrix_ranked.csv", index=False)
    # persist refit candidates for the single test pass (Git-ignored)
    candidates_dir.mkdir(parents=True, exist_ok=True)
    X = project_for_model(train, allow)
    y = train[IS_DROPOUT].astype(int)
    for key, pipe in pipes.items():
        joblib.dump(pipe.fit(X, y), candidates_dir / f"{key}.joblib")
    win = matrix.set_index("candidate").loc[chosen]
    decision = {
        "chosen_candidate": chosen,
        "model": win["model"],
        "selection": win["selection"],
        "best_params": json.loads(win["best_params"]),
        "rule": RULE,
        "eligible_candidates": ranked["candidate"].tolist(),
        "pr_auc_floor": float(
            matrix["pr_auc"].max() - matrix.loc[matrix["pr_auc"].idxmax(), "pr_auc_std_cv"]
        ),
        "chosen_metrics": {
            k: (float(win[k]) if isinstance(win[k], (int, float, np.floating)) else win[k])
            for k in [
                "pr_auc",
                "roc_auc",
                "recall_at_k",
                "precision_at_k",
                "brier",
                "ece",
                "fairness_max_dp_difference",
                "fairness_min_di_ratio",
            ]
        },
        "rationale": (
            f"{chosen} is within one CV standard deviation of the best OOF PR-AUC and ranks "
            "first under the documented lexicographic rule (Recall@K, then ECE, then "
            "demographic-parity gap, then Brier, then fit time). See selection_matrix_ranked.csv."
        ),
        "note": (
            "Validation-based selection on the training split. "
            "Not a test-set result and not a production claim."
        ),
        "n_cohort_expected": n_cohort,
        "seed": cfg.seed,
    }
    (tables_dir / "model_selection_decision.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n"
    )
    return decision


def load_decision(tables_dir: Path) -> dict[str, Any]:
    return json.loads((tables_dir / "model_selection_decision.json").read_text())
