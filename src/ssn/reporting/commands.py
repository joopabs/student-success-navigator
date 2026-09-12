"""CLI handler for `ssn model-card` (registered on import by ssn.cli)."""

from __future__ import annotations

import argparse

from ssn.cli import EXIT_OK, register
from ssn.config import load
from ssn.paths import rel_to_root


@register(None, "model-card")
def cmd_model_card(args: argparse.Namespace) -> int:
    from ssn.reporting import model_card as MC

    cfg = load(args.config, set_seeds=False)
    inputs = MC.load_inputs(cfg)
    text = MC.render(
        inputs["manifest"],
        inputs["test_metrics"],
        inputs["test_k"],
        inputs["fairness"],
        inputs["limitations_md"],
        inputs["explain_method"],
        inputs["out_path"],
    )
    print(f"wrote {rel_to_root(inputs['out_path'], cfg.root)} ({len(text.splitlines())} lines)")
    return EXIT_OK


@register(None, "rubric-map")
def cmd_rubric_map(args: argparse.Namespace) -> int:
    from ssn.reporting import rubric_map as RM

    cfg = load(args.config, set_seeds=False)
    out = cfg.path_for("reports_dir") / "rubric_map.md"
    _, missing = RM.render(cfg.root, out)
    print(f"wrote {rel_to_root(out, cfg.root)}; pending evidence: {missing or 'none'}")
    return EXIT_OK
