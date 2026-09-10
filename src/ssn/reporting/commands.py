"""CLI handler for `ssn model-card` (registered on import by ssn.cli)."""

from __future__ import annotations

import argparse

from ssn.cli import EXIT_OK, register
from ssn.config import load


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
    print(f"wrote {inputs['out_path'].relative_to(cfg.root)} ({len(text.splitlines())} lines)")
    return EXIT_OK
