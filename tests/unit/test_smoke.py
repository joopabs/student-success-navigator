"""Milestone 1 smoke tests: package imports, config parses, scaffold is intact."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

import ssn

REQUIRED_DIRS = [
    "src/ssn/data",
    "src/ssn/features",
    "src/ssn/modeling",
    "src/ssn/explain",
    "src/ssn/fairness",
    "src/ssn/reporting",
    "src/ssn/app",
    "notebooks",
    "data/raw",
    "data/interim",
    "data/processed",
    "data/demo",
    "data/evaluation",
    "data/local",
    "models",
    "reports/figures",
    "reports/decks",
    "tests",
    "configs",
    "docs",
]

IGNORED_SAMPLE_PATHS = [
    "data/raw/data.csv",
    "data/interim/x.parquet",
    "data/processed/x.parquet",
    "data/demo/x.parquet",
    "data/evaluation/x.parquet",
    "data/local/actions.sqlite",
    "data/local/actions_export.csv",
    "models/final_pipeline.joblib",
    "models/candidates/logreg.joblib",
    ".env",
    ".venv/bin/python",
    "notebooks/.ipynb_checkpoints/x.ipynb",
    "references/Pillar5_Capstone_Project.pdf",
]


def test_package_imports_and_has_version() -> None:
    assert ssn.__version__


def test_cli_entry_point_runs() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "ssn", "--version"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0
    assert ssn.__version__ in result.stdout


def test_required_directories_exist(repo_root: Path) -> None:
    missing = [d for d in REQUIRED_DIRS if not (repo_root / d).is_dir()]
    assert not missing, f"missing scaffold directories: {missing}"


def test_base_config_parses_and_capacity_is_consistent(repo_root: Path) -> None:
    cfg = yaml.safe_load((repo_root / "configs" / "base.yaml").read_text())
    for key in (
        "project",
        "seed",
        "paths",
        "data",
        "split",
        "capacity",
        "threshold",
        "imbalance",
        "selection",
        "pca",
        "fairness",
        "explain",
        "app",
        "report",
    ):
        assert key in cfg, f"missing top-level config key: {key}"
    cap = cfg["capacity"]
    assert cap["illustrative"] is True
    assert cap["k"] == cap["per_week"] * cap["window_weeks"]
    assert cfg["project"]["model_version"] == cfg["app"]["expected_model_version"]
    assert cfg["data"]["target_positive_label"] in cfg["data"]["target_expected_labels"]


def test_private_paths_are_gitignored(repo_root: Path) -> None:
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", *IGNORED_SAMPLE_PATHS],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    ignored = set(result.stdout.split())
    not_ignored = [p for p in IGNORED_SAMPLE_PATHS if p not in ignored]
    assert not not_ignored, f"paths that would be committed: {not_ignored}"


def test_gitkeep_placeholders_are_tracked(repo_root: Path) -> None:
    result = subprocess.run(
        ["git", "ls-files", "--others", "--cached", "--exclude-standard", "--", "data", "models"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    visible = set(result.stdout.split())
    for d in (
        "data/raw",
        "data/interim",
        "data/processed",
        "data/demo",
        "data/evaluation",
        "data/local",
        "models",
    ):
        assert f"{d}/.gitkeep" in visible, f"{d}/.gitkeep is ignored or missing"
