"""Command-line interface. Contract: specs/001-dropout-risk-navigator/contracts/cli.md

Exit codes: 0 success; 2 config/validation error or not-yet-implemented; 3 LeakageError;
4 privacy violation.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable, Sequence

from ssn import __version__
from ssn.config import ConfigError, load
from ssn.features.allowlist import LeakageError

EXIT_OK, EXIT_CONFIG, EXIT_LEAKAGE, EXIT_PRIVACY = 0, 2, 3, 4
log = logging.getLogger("ssn")


class PrivacyError(RuntimeError):
    """Adviser-facing output would expose labels, identifiers, or sensitive attributes."""


class NotImplementedCommand(RuntimeError):
    """Command is registered in the contract but not wired yet."""


Handler = Callable[[argparse.Namespace], int]

# (group, command) -> handler. Group None = top-level command.
REGISTRY: dict[tuple[str | None, str], Handler] = {}

CONTRACT_COMMANDS: list[tuple[str | None, str, str]] = [
    ("config", "validate", "Validate configs/base.yaml and print resolved seed and capacity"),
    ("data", "download", "Fetch the UCI CSV and verify its sha256"),
    ("data", "validate", "Check columns, dtypes, Target labels, classification completeness"),
    ("data", "profile", "Write per-column profile tables and configs/ranges.json"),
    ("data", "clean", "Apply documented cleaning; write before/after counts"),
    ("data", "split", "Stratified train/test split; demo cohort and evaluator labels"),
    (None, "eda", "Exploratory analysis figures and tables from train"),
    (None, "select", "Filter + embedded feature selection inside CV"),
    (None, "pca", "PCA comparison inside CV"),
    (None, "train-cv", "Cross-validated comparison of dummy + candidate models"),
    (None, "tune", "RandomizedSearchCV per candidate"),
    (None, "select-model", "Multi-criteria selection matrix and decision"),
    (None, "threshold", "Capacity-aware threshold and bands from OOF scores"),
    (None, "calibrate", "Calibration comparison inside train CV"),
    (None, "fit-final", "Refit selected pipeline on full train; write manifest"),
    (None, "evaluate-test", "Single held-out test evaluation of all models"),
    (None, "explain", "SHAP global/local and PDP/ICE"),
    ("fairness", "audit", "Group fairness metrics with sample sizes"),
    ("fairness", "mitigate", "Mitigation comparison"),
    (None, "model-card", "Render reports/model_card.md"),
    (None, "rubric-map", "Render reports/rubric_map.md"),
    (None, "scan-language", "Scan files for prohibited terms and unlabeled business figures"),
    (None, "reproduce-check", "Compare two run directories and record deltas"),
    (None, "app", "Serve the Student Success Navigator Dash app"),
    ("actions", "export", "Export the local action log to CSV"),
]


def register(group: str | None, name: str) -> Callable[[Handler], Handler]:
    def deco(fn: Handler) -> Handler:
        REGISTRY[(group, name)] = fn
        return fn

    return deco


def _not_implemented(group: str | None, name: str) -> Handler:
    label = f"{group} {name}" if group else name

    def handler(_: argparse.Namespace) -> int:
        raise NotImplementedCommand(
            f"`ssn {label}` is defined in contracts/cli.md but not implemented yet"
        )

    return handler


@register("config", "validate")
def cmd_config_validate(args: argparse.Namespace) -> int:
    cfg = load(args.config)
    cap = cfg.raw["capacity"]
    print(f"config OK: {cfg.path}")
    print(f"seed={cfg.seed}")
    print(
        f"capacity: per_week={cap['per_week']} window_weeks={cap['window_weeks']} "
        f"k={cap['k']} sensitivity_k={cfg.capacity_k_values} illustrative={cap['illustrative']}"
    )
    print(f"model_version={cfg.get('project.model_version')}")
    from ssn.features import allowlist as al

    a = al.load(cfg.path_for("features_yaml"))
    print(
        f"allow-list: allowed={len(a.allowed)} prohibited={len(a.prohibited)} "
        f"sensitive={len(a.sensitive)} ambiguous={len(a.ambiguous)}"
    )
    return EXIT_OK


@register(None, "scan-language")
def cmd_scan_language(args: argparse.Namespace) -> int:
    from ssn.explain import language

    cfg = load(args.config, set_seeds=False)
    rules = language.load(cfg.path_for("language_yaml"))
    findings = language.scan_paths(args.paths, rules)
    for f in findings:
        print(f)
    if findings:
        print(f"scan-language: {len(findings)} finding(s)", file=sys.stderr)
        return 1
    print(f"scan-language: clean ({len(language.iter_files(args.paths))} file(s) scanned)")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ssn", description="Student Success Navigator pipeline and app CLI."
    )
    parser.add_argument("--version", action="version", version=f"ssn {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", default="configs/base.yaml", help="path to base.yaml")
    common.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")
    groups: dict[str, argparse._SubParsersAction] = {}
    for group, name, help_text in CONTRACT_COMMANDS:
        handler = REGISTRY.get((group, name), _not_implemented(group, name))
        if group is None:
            p = sub.add_parser(name, help=help_text, parents=[common])
        else:
            if group not in groups:
                gp = sub.add_parser(group, help=f"{group} commands")
                groups[group] = gp.add_subparsers(dest="subcommand", metavar="<subcommand>")
            p = groups[group].add_parser(name, help=help_text, parents=[common])
        if (group, name) in {(None, "train-cv"), (None, "tune")}:
            p.add_argument("--models", nargs="+", default=None)
        if (group, name) == (None, "train-cv"):
            p.add_argument(
                "--ablation", action="append", choices=["ambiguous", "sensitive"], default=[]
            )
        if (group, name) == ("data", "download"):
            p.add_argument(
                "--from-local",
                default=None,
                help="copy a manually downloaded CSV instead of fetching",
            )
            p.add_argument("--force", action="store_true", help="re-download even if present")
        if (group, name) == (None, "scan-language"):
            p.add_argument("--paths", nargs="+", required=True)
        if (group, name) == (None, "reproduce-check"):
            p.add_argument("--runs-a", required=True)
            p.add_argument("--runs-b", required=True)
            p.add_argument("--tolerance", type=float, default=0.005)
        p.set_defaults(handler=handler)
    return parser


def _load_handlers() -> None:
    """Import modules that register handlers via @register (side-effect imports)."""
    import ssn.data.commands  # noqa: F401
    import ssn.modeling.commands  # noqa: F401


def main(argv: Sequence[str] | None = None) -> int:
    _load_handlers()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "handler", None):
        parser.print_help()
        return EXIT_CONFIG
    logging.basicConfig(
        level=getattr(args, "log_level", "INFO"), format="%(levelname)s %(name)s: %(message)s"
    )
    try:
        return args.handler(args)
    except (ConfigError, NotImplementedCommand) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_CONFIG
    except LeakageError as exc:
        print(f"LEAKAGE: {exc}", file=sys.stderr)
        return EXIT_LEAKAGE
    except PrivacyError as exc:
        print(f"PRIVACY: {exc}", file=sys.stderr)
        return EXIT_PRIVACY
