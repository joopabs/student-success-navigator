"""CLI handlers for modelling-stage commands (registered on import by ssn.cli)."""

from __future__ import annotations

import argparse
import logging

import pandas as pd

from ssn.cli import EXIT_OK, register
from ssn.config import load
from ssn.features import allowlist as al
from ssn.features.preprocess import project_for_model

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
        print(f"wrote {p.relative_to(cfg.root)}")
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
        print(f"wrote {k}: {p.relative_to(cfg.root)}")
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
