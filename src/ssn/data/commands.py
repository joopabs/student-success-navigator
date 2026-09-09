"""CLI handlers for `ssn data ...` commands (registered on import by ssn.cli)."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from ssn.cli import EXIT_OK, register
from ssn.config import load
from ssn.data import profile as P
from ssn.data import schema as S
from ssn.data.download import acquire, sha256_of
from ssn.features import allowlist as al

log = logging.getLogger(__name__)


@register("data", "download")
def cmd_download(args: argparse.Namespace) -> int:
    cfg = load(args.config, set_seeds=False)
    local = Path(args.from_local) if getattr(args, "from_local", None) else None
    path = acquire(cfg, from_local=local, force=bool(getattr(args, "force", False)))
    print(f"raw data ready: {path} sha256={sha256_of(path)}")
    return EXIT_OK


def _load_all(args: argparse.Namespace):
    cfg = load(args.config, set_seeds=False)
    allow = al.load(cfg.path_for("features_yaml"))
    df = S.load_raw(cfg.path_for("raw_csv"))
    return cfg, allow, df


@register("data", "validate")
def cmd_validate(args: argparse.Namespace) -> int:
    cfg, allow, df = _load_all(args)
    report = S.validate(df, cfg, allow)
    out = cfg.path_for("reports_dir") / "tables" / "validate_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report.to_json())
    print(f"rows={report.n_rows} cols={report.n_cols} target={report.target_labels_observed}")
    print(f"classification={report.classification_counts}")
    print(f"report: {out}")
    S.raise_for_errors(report)
    print("schema OK")
    return EXIT_OK


@register("data", "profile")
def cmd_profile(args: argparse.Namespace) -> int:
    from ssn.reporting import tables as T

    cfg, allow, df = _load_all(args)
    report = S.validate(df, cfg, allow)
    prof = P.run_profile(df, cfg, allow)
    tables_dir = cfg.path_for("reports_dir") / "tables"
    written = P.write_outputs(prof, tables_dir, cfg.root / "configs" / "ranges.json")
    dict_path = cfg.root / "data" / "data_dictionary.md"
    overview_path = cfg.path_for("reports_dir") / "data_overview.md"
    T.render_data_dictionary(cfg, allow, prof, report, dict_path)
    T.render_data_overview(
        cfg, allow, prof, report, overview_path, sha256_of(cfg.path_for("raw_csv"))
    )
    for p in [*written, dict_path, overview_path]:
        print(f"wrote {p.relative_to(cfg.root)}")
    if report.errors:
        print("NOTE: schema validation reported errors; see validate_report.json")
    return EXIT_OK
