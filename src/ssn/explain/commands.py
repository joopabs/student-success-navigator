"""CLI handler for `ssn explain` (registered on import by ssn.cli)."""

from __future__ import annotations

import argparse
import json
import logging

import pandas as pd

from ssn.cli import EXIT_OK, register
from ssn.config import load
from ssn.features import allowlist as al
from ssn.features.preprocess import project_for_model
from ssn.paths import rel_to_root

log = logging.getLogger(__name__)


@register(None, "explain")
def cmd_explain(args: argparse.Namespace) -> int:
    from ssn.explain import language as L
    from ssn.explain import pdp_ice as P
    from ssn.explain import shap_explain as S
    from ssn.modeling.persist import MANIFEST_FILE, load_artifact

    cfg = load(args.config)
    allow = al.load(cfg.path_for("features_yaml"))
    models_dir = cfg.path_for("models_dir")
    manifest, final = load_artifact(models_dir, expected_version=cfg.get("project.model_version"))
    test = pd.read_parquet(cfg.path_for("processed_dir") / "test.parquet")
    X = project_for_model(test, allow)
    scores = pd.read_parquet(cfg.path_for("evaluation_dir") / "test_scores_final.parquet")
    out_dir = cfg.path_for("reports_dir") / "explainability"

    res = S.explain_pipeline(final, X, seed=cfg.seed)
    imp = S.global_importance(res)
    examples = S.local_examples(
        res, scores, X, float(manifest["threshold"]["value"]), test["record_id"]
    )
    rules = L.load(cfg.path_for("language_yaml"))
    missing = L.missing_language_entries(rules, allow)
    if missing:
        raise ValueError(f"configs/language.yaml lacks entries for features: {missing}")
    # training medians decide whether a numeric value reads as higher or lower than typical
    from ssn.features.engineering import engineer

    train = pd.read_parquet(cfg.path_for("processed_dir") / "train.parquet")
    Xtr = project_for_model(train, allow)
    reference = pd.concat([Xtr, engineer(Xtr)], axis=1).median(numeric_only=True).to_dict()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "reference_medians_train.json").write_text(
        json.dumps(reference, indent=2, default=float)
    )
    for ex in examples:
        if ex.get("available"):
            ex["adviser_phrases"] = L.render_local(
                ex["top_contributions"], rules, reference=reference
            )
    written = S.write_outputs(
        res,
        imp,
        examples,
        test["record_id"],
        out_dir,
        {"pdp_min_distinct_values": cfg.get("explain.pdp_min_distinct_values")},
    )
    written.append(S.fig_global_bar(imp, out_dir / "shap_global_bar.png"))
    written.append(S.fig_beeswarm(res, X, out_dir / "shap_beeswarm.png"))

    sel = P.select_features(X, allow, int(cfg.get("explain.pdp_min_distinct_values")))
    sel.to_csv(out_dir / "pdp_ice_selection.csv", index=False)
    feats = sel[sel["included"]]["feature"].tolist()
    written += P.plot_pdp_ice(final, X, feats, out_dir, cfg.seed)

    manifest["explainability_files"] = sorted(rel_to_root(p, cfg.root) for p in written)
    (models_dir / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    print(imp.head(15).round(4).to_string(index=False))
    print(f"\nmethod={res.method} members={res.members} pdp_features={len(feats)}")
    for p in written:
        print(f"wrote {rel_to_root(p, cfg.root)}")
    return EXIT_OK
