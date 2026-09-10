"""The single held-out test evaluation (T054, constitution Principle VIII).

Loads the persisted final pipeline, the persisted tuned candidates, and a dummy baseline fitted on
the training split, scores the TEST split ONCE, and writes every FR-012..FR-015 metric for every
model. The manifest's `test_evaluations` counter is incremented so any repeat is visible.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.dummy import DummyClassifier  # noqa: E402

from ssn.config import Config  # noqa: E402
from ssn.features.allowlist import Allowlist  # noqa: E402
from ssn.features.preprocess import project_for_model  # noqa: E402
from ssn.modeling import evaluate as EV  # noqa: E402
from ssn.modeling.persist import MANIFEST_FILE, load_artifact  # noqa: E402
from ssn.modeling.threshold import assign_band, capacity_threshold, k_for_cohort  # noqa: E402

IS_DROPOUT = "is_dropout"
RECORD_ID = "record_id"


def _candidate_threshold(key: str, processed_dir: Path, cfg: Config, n_cohort: int) -> float | None:
    p = processed_dir / f"oof_tuned_{key}.parquet"
    if not p.is_file():
        return None
    oof = pd.read_parquet(p)
    return capacity_threshold(
        oof["score"].to_numpy(), k_for_cohort(int(cfg.get("capacity.k")), len(oof), n_cohort)
    )


def fig_pr(scores: dict[str, np.ndarray], y, path: Path, base_rate: float) -> None:
    fig, ax = plt.subplots(figsize=(7, 5.5))
    for name, s in scores.items():
        c = EV.pr_curve(y, s)
        ax.plot(
            c["recall"],
            c["precision"],
            lw=1.6 if name == "final" else 1.0,
            label=f"{name} (PR-AUC {EV.pr_auc(y, s):.3f})",
        )
    ax.axhline(base_rate, color="gray", ls="--", lw=1, label=f"base rate {base_rate:.3f}")
    ax.set_xlabel("recall")
    ax.set_ylabel("precision")
    ax.set_title("Held-out test precision-recall (single evaluation)")
    ax.legend(fontsize=7)
    fig.text(
        0.01,
        0.005,
        "Source: UCI 697, held-out test split, evaluated once. `python -m ssn evaluate-test`.",
        fontsize=7,
        color="gray",
    )
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130)
    plt.close(fig)


def fig_calibration(y, s, path: Path) -> None:
    rel = EV.reliability_table(y, s).dropna()
    fig, ax = plt.subplots(figsize=(5.5, 5))
    ax.plot([0, 1], [0, 1], color="gray", ls="--", lw=1)
    ax.plot(rel["mean_score"], rel["observed_rate"], marker="o", color="#4c72b0")
    for _, r in rel.iterrows():
        ax.annotate(
            f"n={int(r['n'])}",
            (r["mean_score"], r["observed_rate"]),
            fontsize=6,
            xytext=(3, 3),
            textcoords="offset points",
        )
    ax.set_xlabel("mean predicted score (bin)")
    ax.set_ylabel("observed dropout rate (bin)")
    ax.set_title(
        f"Test reliability, final model (ECE {EV.expected_calibration_error(y, s):.3f}, "
        f"Brier {EV.brier(y, s):.3f})"
    )
    fig.text(
        0.01,
        0.005,
        "Source: UCI 697, held-out test split. `python -m ssn evaluate-test`.",
        fontsize=7,
        color="gray",
    )
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(path, dpi=130)
    plt.close(fig)


def fig_confusion(y, s, thr: float, k: int, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for ax, (title, c) in zip(
        axes,
        (
            (f"at threshold {thr:.3f}", EV.confusion_at_threshold(y, s, thr)),
            (f"at top-K (K={k})", EV.confusion_at_k(y, s, k)),
        ),
        strict=False,
    ):
        m = np.array([[c.tn, c.fp], [c.fn, c.tp]])
        ax.imshow(m, cmap="Blues")
        for i in range(2):
            for j in range(2):
                ax.text(
                    j,
                    i,
                    str(m[i, j]),
                    ha="center",
                    va="center",
                    fontsize=12,
                    color="black" if m[i, j] < m.max() / 2 else "white",
                )
        ax.set_xticks([0, 1], ["pred 0", "pred 1"])
        ax.set_yticks([0, 1], ["true 0", "true 1"])
        ax.set_title(title, fontsize=10)
    fig.suptitle("Held-out test confusion matrices, final model", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def run_evaluate_test(
    test: pd.DataFrame,
    train: pd.DataFrame,
    cfg: Config,
    allow: Allowlist,
    models_dir: Path,
    candidates_dir: Path,
    processed_dir: Path,
    tables_dir: Path,
    figs_dir: Path,
    evaluation_dir: Path,
) -> dict[str, Any]:
    manifest, final = load_artifact(models_dir, expected_version=cfg.get("project.model_version"))
    X = project_for_model(test, allow)
    y = test[IS_DROPOUT].astype(int).to_numpy()
    K = int(cfg.get("capacity.k"))
    n_cohort = int(manifest["threshold"]["n_cohort_expected"])
    k_test = k_for_cohort(K, len(X), n_cohort)
    windows = list(cfg.get("capacity.window_sensitivity_weeks"))
    per_week = int(cfg.get("capacity.per_week"))
    k_values = {f"k{w}w": k_for_cohort(per_week * w, len(X), n_cohort) for w in windows}

    scores: dict[str, np.ndarray] = {"final": final.predict_proba(X)[:, 1]}
    thresholds: dict[str, float] = {"final": float(manifest["threshold"]["value"])}
    Xtr = project_for_model(train, allow)
    dummy = DummyClassifier(strategy="prior", random_state=cfg.seed).fit(
        Xtr, train[IS_DROPOUT].astype(int)
    )
    scores["dummy"] = dummy.predict_proba(X)[:, 1]
    thresholds["dummy"] = float(scores["dummy"][0])  # constant score: threshold = that constant
    for p in sorted(candidates_dir.glob("*.joblib")):
        key = p.stem
        scores[key] = joblib.load(p).predict_proba(X)[:, 1]
        thresholds[key] = _candidate_threshold(key, processed_dir, cfg, n_cohort) or 0.5

    rows = []
    for name, s in scores.items():
        m = EV.metrics_table(y, s, threshold=thresholds[name], k=k_test, k_values=k_values)
        rows.append({"model": name, "threshold": thresholds[name], **m})
    all_models = pd.DataFrame(rows)
    tables_dir.mkdir(parents=True, exist_ok=True)
    all_models.to_csv(tables_dir / "test_metrics_all_models.csv", index=False)
    final_row = all_models[all_models["model"] == "final"].iloc[0]
    all_models[all_models["model"] == "final"].to_csv(tables_dir / "test_metrics.csv", index=False)

    sens = []
    for w in windows:
        kk = per_week * w
        kt = k_for_cohort(kk, len(X), n_cohort)
        rec = EV.recall_at_k(y, scores["final"], kt)
        sens.append(
            {
                "window_weeks": w,
                "capacity_per_week_illustrative": per_week,
                "capacity_k_illustrative": kk,
                "k_applied_to_test": kt,
                "recall_at_k_measured": rec,
                "precision_at_k_measured": EV.precision_at_k(y, scores["final"], kt),
                "share_of_eventual_dropouts_reached_illustrative_kpi": rec,
                "dropouts_in_test": int(y.sum()),
                "note": (
                    "Recall@K is MEASURED on the test split; "
                    "K and the window are ILLUSTRATIVE assumptions"
                ),
            }
        )
    pd.DataFrame(sens).to_csv(tables_dir / "test_recall_precision_at_k.csv", index=False)

    figs_dir.mkdir(parents=True, exist_ok=True)
    fig_pr(scores, y, figs_dir / "test_pr_curve.png", float(y.mean()))
    fig_calibration(y, scores["final"], figs_dir / "test_calibration.png")
    fig_confusion(
        y, scores["final"], thresholds["final"], k_test, figs_dir / "test_confusion_matrix.png"
    )

    evaluation_dir.mkdir(parents=True, exist_ok=True)
    bands = manifest["bands"]
    pd.DataFrame(
        {
            RECORD_ID: test[RECORD_ID].to_numpy(),
            "score": scores["final"],
            IS_DROPOUT: y,
            "band": [assign_band(v, bands) for v in scores["final"]],
        }
    ).to_parquet(evaluation_dir / "test_scores_final.parquet", index=False)

    zero_pos = bool(final_row["thr_tp"] == 0)
    manifest["test_evaluations"] = int(manifest.get("test_evaluations", 0)) + 1
    manifest["test_summary"] = {
        k: float(final_row[k])
        for k in ["pr_auc", "roc_auc", "recall_at_k", "precision_at_k", "brier", "ece"]
    }
    manifest["test_summary"]["k_applied_to_test"] = int(k_test)
    manifest["data"]["n_test"] = int(len(X))
    manifest["data"]["positive_rate_test"] = round(float(y.mean()), 4)
    manifest["zero_predicted_positives_on_test"] = zero_pos
    manifest["test_evaluated_at"] = pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    (models_dir / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    return {
        "all_models": all_models,
        "final": final_row.to_dict(),
        "test_evaluations": manifest["test_evaluations"],
        "zero_predicted_positives": zero_pos,
        "k_test": k_test,
    }
