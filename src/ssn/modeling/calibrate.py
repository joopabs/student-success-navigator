"""Calibration comparison (T052, research R-10).

Uncalibrated tuned pipeline vs CalibratedClassifierCV (isotonic, sigmoid) with inner cv=5, all
evaluated by OUTER out-of-fold prediction on the training split. Rule: apply calibration only if
Brier improves and PR-AUC does not fall by more than one CV standard deviation. Writes the OOF
scores of the chosen final variant to processed/oof_final.parquet for the threshold step.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.base import clone  # noqa: E402
from sklearn.calibration import CalibratedClassifierCV  # noqa: E402

from ssn.config import Config  # noqa: E402
from ssn.features.allowlist import Allowlist  # noqa: E402
from ssn.features.preprocess import project_for_model  # noqa: E402
from ssn.modeling import evaluate as EV  # noqa: E402
from ssn.modeling.cv import make_cv, oof_predict  # noqa: E402
from ssn.modeling.threshold import capacity_threshold, k_for_cohort  # noqa: E402

IS_DROPOUT = "is_dropout"
RECORD_ID = "record_id"
METHODS = ("isotonic", "sigmoid")


def wrap_calibrated(pipeline, method: str, cv: int = 5):
    return CalibratedClassifierCV(estimator=clone(pipeline), method=method, cv=cv, ensemble=True)


def _summary(name: str, y, s, k: int, pr_std: float) -> dict[str, Any]:
    return {
        "variant": name,
        "pr_auc": EV.pr_auc(y, s),
        "pr_auc_std_cv_uncalibrated": pr_std,
        "roc_auc": EV.roc_auc(y, s),
        "brier": EV.brier(y, s),
        "ece": EV.expected_calibration_error(y, s),
        "recall_at_k": EV.recall_at_k(y, s, k),
        "precision_at_k": EV.precision_at_k(y, s, k),
        "mean_score": float(pd.Series(s).mean()),
    }


def fig_reliability(curves: dict[str, pd.DataFrame], path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.plot([0, 1], [0, 1], color="gray", ls="--", lw=1, label="perfectly calibrated")
    for name, frame in curves.items():
        rel = EV.reliability_table(frame["y_true"], frame["score"]).dropna()
        ece = EV.expected_calibration_error(frame["y_true"], frame["score"])
        ax.plot(
            rel["mean_score"],
            rel["observed_rate"],
            marker="o",
            ms=4,
            lw=1.2,
            label=f"{name} (ECE {ece:.3f})",
        )
    ax.set_xlabel("mean predicted score (bin)")
    ax.set_ylabel("observed dropout rate (bin)")
    ax.set_title("OOF reliability: uncalibrated vs calibrated (training split)")
    ax.legend(fontsize=8)
    fig.text(
        0.01,
        0.005,
        "Source: UCI 697, training split, OOF. `python -m ssn calibrate`.",
        fontsize=7,
        color="gray",
    )
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def run_calibration(
    train: pd.DataFrame,
    pipeline,
    uncal_oof: pd.DataFrame,
    pr_std: float,
    cfg: Config,
    allow: Allowlist,
    n_cohort: int,
    tables_dir: Path,
    figs_dir: Path,
    processed_dir: Path,
) -> dict[str, Any]:
    X = project_for_model(train, allow)
    y = train[IS_DROPOUT].astype(int)
    k_train = k_for_cohort(int(cfg.get("capacity.k")), len(X), n_cohort)
    rows = [_summary("uncalibrated", uncal_oof["y_true"], uncal_oof["score"], k_train, pr_std)]
    curves = {"uncalibrated": uncal_oof}
    oofs = {}
    for method in METHODS:
        oof = oof_predict(wrap_calibrated(pipeline, method), X, y, make_cv(cfg))
        frame = oof.frame(train[RECORD_ID] if RECORD_ID in train.columns else None)
        oofs[method] = frame
        curves[method] = frame
        rows.append(_summary(method, frame["y_true"], frame["score"], k_train, pr_std))
    table = pd.DataFrame(rows)
    base = table.iloc[0]
    cands = table.iloc[1:]
    better = cands[(cands["brier"] < base["brier"]) & (cands["pr_auc"] >= base["pr_auc"] - pr_std)]
    if better.empty:
        applied, method = False, None
        final_oof = uncal_oof
    else:
        method = str(better.sort_values("brier").iloc[0]["variant"])
        applied = True
        final_oof = oofs[method]
    decision = {
        "applied": applied,
        "method": method,
        "rule": (
            "apply the calibration method with the lowest Brier if it beats the uncalibrated "
            "Brier and its PR-AUC is not lower than uncalibrated PR-AUC minus one CV std"
        ),
        "uncalibrated": {k: float(base[k]) for k in ["pr_auc", "brier", "ece", "recall_at_k"]},
        "chosen": None
        if method is None
        else {
            k: float(table.set_index("variant").loc[method, k])
            for k in ["pr_auc", "brier", "ece", "recall_at_k"]
        },
        "inner_cv": 5,
        "note": (
            "Calibration affects probability quality, not ranking-based Recall@K. "
            "Evaluated on the training split only."
        ),
    }
    tables_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(tables_dir / "calibration_comparison.csv", index=False)
    (tables_dir / "calibration_decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    fig_reliability(curves, figs_dir / "oof_calibration.png")
    final_oof.reset_index(drop=True).to_parquet(processed_dir / "oof_final.parquet", index=False)
    return decision


def load_calibration_decision(tables_dir: Path) -> dict[str, Any]:
    return json.loads((tables_dir / "calibration_decision.json").read_text())


def capacity_threshold_for(oof: pd.DataFrame, cfg: Config, n_cohort: int) -> float:
    k = k_for_cohort(int(cfg.get("capacity.k")), len(oof), n_cohort)
    return capacity_threshold(oof["score"].to_numpy(), k)
