"""CLI handlers for `ssn app` and `ssn actions export` (registered on import by ssn.cli)."""

from __future__ import annotations

import argparse

from ssn.cli import EXIT_OK, register
from ssn.config import load


@register(None, "app")
def cmd_app(args: argparse.Namespace) -> int:
    from ssn.app.app import create_app

    cfg = load(args.config, set_seeds=False)
    app = create_app(cfg)
    print(
        f"Student Success Navigator at http://{cfg.get('app.host')}:{cfg.get('app.port')}  (Ctrl+C to stop)"
    )
    app.run(host=str(cfg.get("app.host")), port=int(cfg.get("app.port")), debug=False)
    return EXIT_OK


@register("actions", "export")
def cmd_actions_export(args: argparse.Namespace) -> int:
    from ssn.app.services.action_log import ActionLog

    cfg = load(args.config, set_seeds=False)
    log = ActionLog(cfg.path_for("app.actions_db"))
    out = log.export_csv(cfg.path_for("local_dir") / "actions_export.csv")
    print(f"exported {log.count()} rows to {out} (local only; Git-ignored)")
    return EXIT_OK
