"""CLI handlers for modelling-stage commands (registered on import by ssn.cli)."""

from __future__ import annotations

import argparse
import logging

import pandas as pd

from ssn.cli import EXIT_OK, register
from ssn.config import load
from ssn.features import allowlist as al
from ssn.features.preprocess import project_for_model
from ssn.paths import rel_to_root

log = logging.getLogger(__name__)
IS_DROPOUT = "is_dropout"


def load_train(cfg, allow):
    """Read the TRAINING split only and project to allow-listed model inputs."""
    path = cfg.path_for("processed_dir") / "train.parquet"
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found; run `python -m ssn data split` first")
    train = pd.read_parquet(path)
    X = project_for_model(train, allow)
    y = train[IS_DROPOUT].astype(int)
    return train, X, y


@register(None, "select")
def cmd_select(args: argparse.Namespace) -> int:
    from ssn.modeling import selection as SEL

    cfg = load(args.config)
    allow = al.load(cfg.path_for("features_yaml"))
    _, X, y = load_train(cfg, allow)
    methods = SEL.configured_methods(cfg)
    log.info("CV over k grid %s for %s", cfg.get("selection.k_grid"), methods)
    cv_table = SEL.cv_by_k(X, y, cfg, allow, methods)
    scores = SEL.describe_scores(X, y, cfg, allow, methods)
    n_features = len(scores["filter"])
    decision = SEL.decide(cv_table, cfg, n_features)
    written = SEL.write_outputs(cfg.path_for("reports_dir") / "tables", cv_table, scores, decision)
    print(cv_table.round(4).to_string(index=False))
    print(decision.to_json())
    for p in written:
        print(f"wrote {rel_to_root(p, cfg.root)}")
    return EXIT_OK


@register(None, "pca")
def cmd_pca(args: argparse.Namespace) -> int:
    from ssn.modeling import pca as P

    cfg = load(args.config)
    allow = al.load(cfg.path_for("features_yaml"))
    _, X, y = load_train(cfg, allow)
    out = P.run_pca(
        X,
        y,
        cfg,
        allow,
        cfg.path_for("reports_dir") / "tables",
        cfg.path_for("reports_dir") / "figures",
    )
    print(pd.read_csv(out["compare"]).round(4).to_string(index=False))
    for k, p in out.items():
        print(f"wrote {k}: {rel_to_root(p, cfg.root)}")
    return EXIT_OK


@register(None, "train-cv")
def cmd_train_cv(args: argparse.Namespace) -> int:
    from ssn.modeling import traincv as TC

    cfg = load(args.config)
    allow = al.load(cfg.path_for("features_yaml"))
    train, _, _ = load_train(cfg, allow)
    models = args.models or list(TC.CANDIDATES)
    table, _ = TC.run_train_cv(train, cfg, allow, models)
    show = [
        "variant",
        "pr_auc_mean",
        "pr_auc_std",
        "roc_auc_mean",
        "recall_at_k_mean",
        "precision_at_k_mean",
        "brier_mean",
        "ece_mean",
        "fit_time_s_mean",
    ]
    print(table[show].round(4).to_string(index=False))
    tables = cfg.path_for("reports_dir") / "tables"
    for which in args.ablation or []:
        abl = TC.run_ablation(train, cfg, allow, which, models, table)
        abl.to_csv(tables / f"ablation_{which}.csv", index=False)
        print(f"\nablation: {which}")
        print(abl.round(4).to_string(index=False))
    print(
        f"\nwrote {tables / 'cv_comparison.csv'} and OOF parquet files under "
        f"{cfg.path_for('processed_dir')}"
    )
    return EXIT_OK


def _dirs(cfg):
    return {
        "tables": cfg.path_for("reports_dir") / "tables",
        "figs": cfg.path_for("reports_dir") / "figures",
        "processed": cfg.path_for("processed_dir"),
        "models": cfg.path_for("models_dir"),
        "candidates": cfg.path_for("models_dir") / "candidates",
        "evaluation": cfg.path_for("evaluation_dir"),
    }


@register(None, "tune")
def cmd_tune(args: argparse.Namespace) -> int:
    from ssn.modeling import tune as TU
    from ssn.modeling.traincv import load_selection_setting

    cfg = load(args.config)
    allow = al.load(cfg.path_for("features_yaml"))
    _, X, y = load_train(cfg, allow)
    models = args.models or ["logreg", "random_forest", "hist_gb"]
    tuned = TU.run_tuning(
        X, y, cfg, allow, models, load_selection_setting(cfg), _dirs(cfg)["tables"]
    )
    for k, v in tuned.items():
        print(
            f"{k}: PR-AUC {v['cv_pr_auc_mean']:.4f} +/- {v['cv_pr_auc_std']:.4f} params={v['best_params']}"
        )
    return EXIT_OK


@register(None, "select-model")
def cmd_select_model(args: argparse.Namespace) -> int:
    from ssn.modeling import select_model as SM
    from ssn.modeling.tune import load_tuned

    cfg = load(args.config)
    allow = al.load(cfg.path_for("features_yaml"))
    train, _, _ = load_train(cfg, allow)
    d = _dirs(cfg)
    decision = SM.run_select_model(
        train, cfg, allow, load_tuned(d["tables"]), d["tables"], d["processed"], d["candidates"]
    )
    print(pd.read_csv(d["tables"] / "selection_matrix_ranked.csv").round(4).to_string(index=False))
    print(f"\nchosen: {decision['chosen_candidate']}\n{decision['rationale']}")
    return EXIT_OK


@register(None, "calibrate")
def cmd_calibrate(args: argparse.Namespace) -> int:
    from ssn.modeling import calibrate as CAL
    from ssn.modeling import select_model as SM
    from ssn.modeling.traincv import expected_cohort_size, load_selection_setting
    from ssn.modeling.tune import load_tuned

    cfg = load(args.config)
    allow = al.load(cfg.path_for("features_yaml"))
    train, _, _ = load_train(cfg, allow)
    d = _dirs(cfg)
    decision = SM.load_decision(d["tables"])
    key = decision["chosen_candidate"]
    pipe = SM.tuned_pipeline(key, load_tuned(d["tables"]), cfg, allow, load_selection_setting(cfg))
    uncal = pd.read_parquet(d["processed"] / f"oof_tuned_{key}.parquet")
    pr_std = float(
        pd.read_csv(d["tables"] / "selection_matrix.csv")
        .set_index("candidate")
        .loc[key, "pr_auc_std_cv"]
    )
    out = CAL.run_calibration(
        train,
        pipe,
        uncal,
        pr_std,
        cfg,
        allow,
        expected_cohort_size(cfg),
        d["tables"],
        d["figs"],
        d["processed"],
    )
    print(pd.read_csv(d["tables"] / "calibration_comparison.csv").round(4).to_string(index=False))
    print(f"\ncalibration applied: {out['applied']} method: {out['method']}")
    return EXIT_OK


@register(None, "threshold")
def cmd_threshold(args: argparse.Namespace) -> int:
    from ssn.modeling import threshold as TH
    from ssn.modeling.traincv import expected_cohort_size

    cfg = load(args.config)
    d = _dirs(cfg)
    oof_path = d["processed"] / "oof_final.parquet"
    if not oof_path.is_file():
        raise FileNotFoundError(f"{oof_path} not found; run `python -m ssn calibrate` first")
    res = TH.run_threshold(pd.read_parquet(oof_path), cfg, expected_cohort_size(cfg), d["tables"])
    print(pd.read_csv(d["tables"] / "threshold_tradeoffs.csv").round(4).to_string(index=False))
    print(
        f"\nthreshold={res['threshold']:.4f} (k={res['k_scaled_to_oof']} of {res['n_oof_rows']} OOF rows) bands:"
    )
    for b in res["bands"]:
        print(
            f"  {b['name']}: [{b['lower']:.4f}, {b['upper']:.4f}]  share_oof={res['band_shares_oof'][b['name']]:.3f}"
        )
    if res["zero_predicted_positives"]:
        print("WARNING: zero predicted positives at the capacity threshold (spec edge case)")
    return EXIT_OK


@register(None, "fit-final")
def cmd_fit_final(args: argparse.Namespace) -> int:
    import json

    from ssn.data.download import sha256_of
    from ssn.modeling import persist as PS
    from ssn.modeling import select_model as SM
    from ssn.modeling.calibrate import load_calibration_decision
    from ssn.modeling.threshold import load_threshold
    from ssn.modeling.traincv import load_selection_setting

    cfg = load(args.config)
    allow = al.load(cfg.path_for("features_yaml"))
    train, _, _ = load_train(cfg, allow)
    d = _dirs(cfg)
    decision = SM.load_decision(d["tables"])
    matrix_row = (
        pd.read_csv(d["tables"] / "selection_matrix.csv")
        .set_index("candidate")
        .loc[decision["chosen_candidate"]]
        .to_dict()
    )
    ranges_path = cfg.root / "configs" / "ranges.json"
    ranges = json.loads(ranges_path.read_text()) if ranges_path.is_file() else None
    manifest = PS.fit_and_persist(
        train,
        cfg,
        allow,
        decision,
        load_calibration_decision(d["tables"]),
        load_threshold(d["tables"]),
        matrix_row,
        load_selection_setting(cfg),
        d["models"],
        sha256_of(cfg.path_for("raw_csv")),
        ranges,
    )
    print(
        f"persisted {manifest['pipeline_file']} sha256={manifest['pipeline_sha256'][:16]}... version={manifest['model_version']}"
    )
    print(
        f"estimator={manifest['estimator']['class']} calibration={manifest['calibration']} threshold={manifest['threshold']['value']:.4f}"
    )
    return EXIT_OK


@register(None, "evaluate-test")
def cmd_evaluate_test(args: argparse.Namespace) -> int:
    import warnings

    from ssn.modeling import evaluate_test as ET

    cfg = load(args.config)
    allow = al.load(cfg.path_for("features_yaml"))
    train, _, _ = load_train(cfg, allow)
    d = _dirs(cfg)
    test = pd.read_parquet(
        d["processed"] / "test.parquet"
    )  # the ONLY command that reads test labels for metrics
    out = ET.run_evaluate_test(
        test,
        train,
        cfg,
        allow,
        d["models"],
        d["candidates"],
        d["processed"],
        d["tables"],
        d["figs"],
        d["evaluation"],
    )
    show = [
        "model",
        "threshold",
        "pr_auc",
        "roc_auc",
        "recall_at_k",
        "precision_at_k",
        "brier",
        "ece",
        "precision_at_threshold",
        "recall_at_threshold",
        "f1_at_threshold",
    ]
    print(out["all_models"][show].round(4).to_string(index=False))
    print(
        f"\ntest_evaluations={out['test_evaluations']} k_test={out['k_test']} zero_predicted_positives={out['zero_predicted_positives']}"
    )
    if out["test_evaluations"] > 1:
        warnings.warn(
            "held-out test set has been evaluated more than once; disclosed in the manifest and model card",
            stacklevel=1,
        )
    return EXIT_OK


@register(None, "reproduce-check")
def cmd_reproduce_check(args: argparse.Namespace) -> int:
    from pathlib import Path

    from ssn.modeling import reproduce as RP

    cfg = load(args.config, set_seeds=False)
    a, b = Path(args.runs_a), Path(args.runs_b)
    ta = a / "tables" if (a / "tables").is_dir() else a
    tb = b / "tables" if (b / "tables").is_dir() else b
    deltas = RP.compare_runs(ta, tb)
    out = cfg.path_for("report.reproduction_tolerance_file")
    ok = RP.write_report(deltas, float(args.tolerance), out, str(a), str(b))
    print(deltas.sort_values("max_abs_delta", ascending=False).head(10).to_string(index=False))
    print(f"\nwrote {out}; PASS={ok}")
    return EXIT_OK if ok else 1
