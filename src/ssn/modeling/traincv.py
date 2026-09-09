"""Cross-validated comparison of the dummy baseline and candidate models (T044).

Reads the TRAINING split only. For every (model, selection, imbalance) variant it fits a fresh
pipeline per fold, keeps out-of-fold scores, and computes PR-AUC (primary), ROC-AUC, Brier, ECE,
precision/recall/F1/accuracy at 0.5, Recall@K and Precision@K for the illustrative capacity K
scaled to the fold, and confusion matrices. Fold means and standard deviations go to
`cv_comparison.csv`; OOF scores are persisted for the threshold work in Milestone 6.

No model is selected here. Accuracy is reported for transparency but is excluded from the
selection matrix in Milestone 6 (constitution Principle VIII).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.base import clone  # noqa: E402

from ssn.config import Config, load_model_config  # noqa: E402
from ssn.features import allowlist as al  # noqa: E402
from ssn.features.allowlist import Allowlist  # noqa: E402
from ssn.features.preprocess import project_for_model  # noqa: E402
from ssn.modeling import evaluate as EV  # noqa: E402
from ssn.modeling.candidates import (  # noqa: E402
    SelectionSetting,
    build_pipeline,
    describe,
)
from ssn.modeling.cv import k_for_fold, make_cv  # noqa: E402

IS_DROPOUT = "is_dropout"
RECORD_ID = "record_id"
DEFAULT_THRESHOLD = 0.5
SMOTE_MODELS = {"logreg", "random_forest"}  # research R-07


@dataclass(frozen=True)
class Variant:
    model: str
    selection: str  # "none" | "decided"
    imbalance: str  # "class_weight" | "smotenc" | "none"

    @property
    def key(self) -> str:
        return f"{self.model}__sel-{self.selection}__imb-{self.imbalance}"


def expected_cohort_size(cfg: Config) -> int:
    """Test cohort size from split_summary.csv (computed), else derived from test_size."""
    p = cfg.path_for("reports_dir") / "tables" / "split_summary.csv"
    if p.is_file():
        s = pd.read_csv(p)
        row = s[s["split"] == "test"]
        if not row.empty:
            return int(row["n"].iloc[0])
    return 885  # documented fallback: 0.2 * 4424 rounded (data/README.md)


def load_selection_setting(cfg: Config) -> SelectionSetting | None:
    p = cfg.path_for("reports_dir") / "tables" / "selection_decision.json"
    if not p.is_file():
        return None
    d = json.loads(p.read_text())
    return SelectionSetting(kind=d["kind"], method=d["method"], k=d["k"])


def variants_for(
    models: list[str], cfg: Config, selection: SelectionSetting | None
) -> list[Variant]:
    out: list[Variant] = []
    for m in models:
        if m == "dummy":
            out.append(Variant("dummy", "none", "none"))
            continue
        mc = load_model_config(m, cfg)
        sels = ["none", "decided"] if (mc.use_selection and selection is not None) else ["none"]
        imbs = ["class_weight"]
        if cfg.get("imbalance.compare_smote") and m in SMOTE_MODELS:
            imbs.append("smotenc")
        for s in sels:
            for i in imbs:
                out.append(Variant(m, s, i))
    return out


def _pipeline_for(v: Variant, cfg: Config, allow: Allowlist, selection: SelectionSetting | None):
    return build_pipeline(
        v.model,
        cfg,
        allow,
        selection=selection if v.selection == "decided" else None,
        smote=(v.imbalance == "smotenc"),
    )


def run_variant(
    v: Variant,
    X: pd.DataFrame,
    y: pd.Series,
    cfg: Config,
    allow: Allowlist,
    selection: SelectionSetting | None,
    n_cohort: int,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Fold loop for one variant. Returns (summary row, OOF frame)."""
    cv = make_cv(cfg)
    K = int(cfg.get("capacity.k"))
    k_alt = {
        f"k{w}w": cfg.get("capacity.per_week") * w
        for w in cfg.get("capacity.window_sensitivity_weeks")
    }
    pipe = _pipeline_for(v, cfg, allow, selection)
    y_arr = np.asarray(y).astype(int)
    oof = np.full(len(X), np.nan)
    folds = np.full(len(X), -1)
    per_fold: list[dict[str, float]] = []
    fit_times: list[float] = []
    for fold, (tr, va) in enumerate(cv.split(X, y_arr)):
        t0 = time.perf_counter()
        model = clone(pipe).fit(X.iloc[tr], y_arr[tr])
        fit_times.append(time.perf_counter() - t0)
        s = model.predict_proba(X.iloc[va])[:, 1]
        oof[va] = s
        folds[va] = fold
        k_fold = k_for_fold(K, len(va), n_cohort)
        k_alt_fold = {lbl: k_for_fold(kk, len(va), n_cohort) for lbl, kk in k_alt.items()}
        per_fold.append(
            EV.metrics_table(
                y_arr[va], s, threshold=DEFAULT_THRESHOLD, k=k_fold, k_values=k_alt_fold
            )
        )
    pf = pd.DataFrame(per_fold)
    mc = load_model_config(v.model, cfg)
    row: dict[str, Any] = {
        "model": v.model,
        "selection": v.selection,
        "imbalance": v.imbalance,
        "variant": v.key,
        **describe(pipe, v.model, mc),
        "seed": cfg.seed,
        "n_folds": cv.get_n_splits(),
        "n_train": int(len(X)),
        "capacity_k": K,
        "n_cohort_expected": n_cohort,
        "fit_time_s_mean": float(np.mean(fit_times)),
        "fit_time_s_total": float(np.sum(fit_times)),
    }
    for col in pf.columns:
        if col.startswith(("thr_", "topk_")):
            row[f"{col}_sum"] = int(pf[col].sum())
        elif col == "k":
            row["k_fold_mean"] = float(pf[col].mean())
        else:
            row[f"{col}_mean"] = float(pf[col].mean())
            row[f"{col}_std"] = float(pf[col].std(ddof=1))
    oof_frame = pd.DataFrame({"fold": folds, "y_true": y_arr, "score": oof}, index=X.index)
    return row, oof_frame


def fig_pr_curves(oofs: dict[str, pd.DataFrame], path: Path, base_rate: float) -> Path:
    fig, ax = plt.subplots(figsize=(7, 5.5))
    for key, frame in oofs.items():
        curve = EV.pr_curve(frame["y_true"], frame["score"])
        ap = EV.pr_auc(frame["y_true"], frame["score"])
        ax.plot(curve["recall"], curve["precision"], lw=1.6, label=f"{key} (OOF PR-AUC {ap:.3f})")
    ax.axhline(base_rate, color="gray", ls="--", lw=1, label=f"base rate {base_rate:.3f}")
    ax.set_xlabel("recall")
    ax.set_ylabel("precision")
    ax.set_title("Out-of-fold precision-recall curves (5-fold CV, training split)")
    ax.legend(fontsize=7)
    fig.text(
        0.01,
        0.005,
        "Source: UCI 697, training split, OOF predictions. `python -m ssn train-cv`.",
        fontsize=7,
        color="gray",
    )
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def fig_calibration(oofs: dict[str, pd.DataFrame], path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.plot([0, 1], [0, 1], color="gray", ls="--", lw=1, label="perfectly calibrated")
    for key, frame in oofs.items():
        rel = EV.reliability_table(frame["y_true"], frame["score"]).dropna()
        ece = EV.expected_calibration_error(frame["y_true"], frame["score"])
        ax.plot(
            rel["mean_score"],
            rel["observed_rate"],
            marker="o",
            ms=4,
            lw=1.2,
            label=f"{key} (ECE {ece:.3f})",
        )
    ax.set_xlabel("mean predicted score (bin)")
    ax.set_ylabel("observed dropout rate (bin)")
    ax.set_title("Out-of-fold reliability curves (uncalibrated candidates)")
    ax.legend(fontsize=7)
    fig.text(
        0.01,
        0.005,
        "Source: UCI 697, training split, OOF predictions. `python -m ssn train-cv`.",
        fontsize=7,
        color="gray",
    )
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def run_train_cv(
    train: pd.DataFrame,
    cfg: Config,
    allow: Allowlist,
    models: list[str],
    *,
    write: bool = True,
    tag: str = "",
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """Compare variants under CV. Returns (comparison table, OOF frames keyed by variant)."""
    if "dummy" not in models:
        models = ["dummy", *models]
    X = project_for_model(train, allow)
    y = train[IS_DROPOUT].astype(int)
    selection = load_selection_setting(cfg)
    n_cohort = expected_cohort_size(cfg)
    rows, oofs = [], {}
    for v in variants_for(models, cfg, selection):
        row, oof = run_variant(v, X, y, cfg, allow, selection, n_cohort)
        rows.append(row)
        if RECORD_ID in train.columns:
            oof.insert(0, RECORD_ID, train[RECORD_ID].to_numpy())
        oofs[v.key] = oof
    table = pd.DataFrame(rows)
    if write:
        tables = cfg.path_for("reports_dir") / "tables"
        figs = cfg.path_for("reports_dir") / "figures"
        tables.mkdir(parents=True, exist_ok=True)
        table.to_csv(tables / f"cv_comparison{tag}.csv", index=False)
        conf_cols = [c for c in table.columns if c.startswith(("thr_", "topk_"))]
        table[["variant", *conf_cols]].to_csv(tables / f"cv_confusion{tag}.csv", index=False)
        processed = cfg.path_for("processed_dir")
        for key, oof in oofs.items():
            oof.reset_index(drop=True).to_parquet(
                processed / f"oof_{key}{tag}.parquet", index=False
            )
        default = {k: f for k, f in oofs.items() if "sel-none" in k and "smotenc" not in k}
        fig_pr_curves(default, figs / f"cv_pr_curves{tag}.png", float(y.mean()))
        fig_calibration(
            {k: f for k, f in default.items() if not k.startswith("dummy")},
            figs / f"cv_calibration{tag}.png",
        )
    return table, oofs


def promoted_allowlist(cfg: Config, which: str) -> Allowlist:
    """Allow-list with `ambiguous` or `sensitive` columns temporarily promoted to model features.
    ANALYSIS ONLY for ablations; never used to build a persisted candidate."""
    import yaml

    raw = yaml.safe_load(Path(cfg.path_for("features_yaml")).read_text())
    for col in raw["columns"]:
        if which == "ambiguous" and col["availability"] == "ambiguous":
            col["availability"] = "enrollment"
        if which == "sensitive" and col["role"] == "sensitive":
            col["role"] = "feature"
    return al.build(raw)


def run_ablation(
    train: pd.DataFrame,
    cfg: Config,
    allow: Allowlist,
    which: str,
    models: list[str],
    baseline: pd.DataFrame,
) -> pd.DataFrame:
    """Default variants (no selection, class weighting) with promoted columns vs baseline."""
    promoted = promoted_allowlist(cfg, which)
    X = project_for_model(train, promoted)
    y = train[IS_DROPOUT].astype(int)
    n_cohort = expected_cohort_size(cfg)
    rows = []
    for m in [x for x in models if x != "dummy"]:
        v = Variant(m, "none", "class_weight")
        row, _ = run_variant(v, X, y, cfg, promoted, None, n_cohort)
        base = baseline[
            (baseline["model"] == m)
            & (baseline["selection"] == "none")
            & (baseline["imbalance"] == "class_weight")
        ]
        b = base.iloc[0] if not base.empty else None
        rows.append(
            {
                "ablation": which,
                "model": m,
                "columns_added": len(X.columns) - len(project_for_model(train, allow).columns),
                "pr_auc_mean_with": row["pr_auc_mean"],
                "pr_auc_std_with": row["pr_auc_std"],
                "pr_auc_mean_without": None if b is None else b["pr_auc_mean"],
                "delta_pr_auc": None if b is None else row["pr_auc_mean"] - b["pr_auc_mean"],
                "recall_at_k_mean_with": row["recall_at_k_mean"],
                "recall_at_k_mean_without": None if b is None else b["recall_at_k_mean"],
                "delta_recall_at_k": None
                if b is None
                else row["recall_at_k_mean"] - b["recall_at_k_mean"],
                "note": "analysis only; promoted columns are NOT allowed for the deployed model",
            }
        )
    return pd.DataFrame(rows)
