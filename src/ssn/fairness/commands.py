"""CLI handlers for `ssn fairness audit|mitigate` (registered on import by ssn.cli)."""

from __future__ import annotations

import argparse
import logging

import pandas as pd

from ssn.cli import EXIT_OK, register
from ssn.config import load
from ssn.features import allowlist as al

log = logging.getLogger(__name__)


@register("fairness", "audit")
def cmd_fairness_audit(args: argparse.Namespace) -> int:
    from ssn.fairness import audit as A
    from ssn.modeling.persist import load_artifact

    cfg = load(args.config)
    allow = al.load(cfg.path_for("features_yaml"))
    manifest, _ = load_artifact(
        cfg.path_for("models_dir"), expected_version=cfg.get("project.model_version")
    )
    scores = pd.read_parquet(cfg.path_for("evaluation_dir") / "test_scores_final.parquet")
    labels = pd.read_parquet(cfg.path_for("evaluation_dir") / "demo_cohort_labels.parquet")
    k = int(manifest["test_summary"].get("k_applied_to_test") or cfg.get("capacity.k"))
    out = A.run_audit(
        scores,
        labels,
        cfg,
        allow,
        float(manifest["threshold"]["value"]),
        k,
        cfg.path_for("reports_dir") / "fairness",
    )
    summary = pd.DataFrame(out["attribute_summary"])
    print(summary.round(4).to_string(index=False))
    groups = pd.DataFrame(out["groups"])
    print(
        groups[
            [
                "attribute",
                "operating_point",
                "group",
                "n",
                "reliable",
                "base_rate",
                "selection_rate",
                "tpr",
                "fpr",
                "brier",
            ]
        ]
        .round(4)
        .to_string(index=False)
    )
    return EXIT_OK


@register("fairness", "mitigate")
def cmd_fairness_mitigate(args: argparse.Namespace) -> int:
    from ssn.fairness import mitigate as M
    from ssn.modeling import select_model as SM
    from ssn.modeling.traincv import expected_cohort_size, load_selection_setting
    from ssn.modeling.tune import load_tuned

    cfg = load(args.config)
    allow = al.load(cfg.path_for("features_yaml"))
    tables = cfg.path_for("reports_dir") / "tables"
    train = pd.read_parquet(cfg.path_for("processed_dir") / "train.parquet")
    decision = SM.load_decision(tables)
    key = decision["chosen_candidate"]
    pipe = SM.tuned_pipeline(key, load_tuned(tables), cfg, allow, load_selection_setting(cfg))
    baseline_oof = pd.read_parquet(cfg.path_for("processed_dir") / f"oof_tuned_{key}.parquet")
    table = M.run_mitigation(
        train,
        pipe,
        baseline_oof,
        cfg,
        allow,
        expected_cohort_size(cfg),
        cfg.path_for("reports_dir") / "fairness",
    )
    print(table.drop(columns=["note"]).round(4).to_string(index=False))
    return EXIT_OK
