"""`rel_to_root` must not raise for output paths outside the repository.

Output directories are config-driven, so a second pipeline run for `reproduce-check` (or a pytest
`tmp_path`) legitimately writes outside the repository. The display helper previously used
`Path.relative_to` directly, which raises `ValueError` in that case — and did so *after* the command
had written its files, so commands exited non-zero having produced correct output.
"""

from __future__ import annotations

from pathlib import Path

from ssn.paths import rel_to_root


def test_path_inside_root_is_reported_relative(repo_root: Path) -> None:
    assert rel_to_root(repo_root / "reports" / "tables" / "x.csv", repo_root) == "reports/tables/x.csv"


def test_path_outside_root_falls_back_to_absolute(repo_root: Path, tmp_path: Path) -> None:
    outside = tmp_path / "run2" / "reports" / "x.csv"
    assert rel_to_root(outside, repo_root) == str(outside)


def test_outside_root_does_not_raise(repo_root: Path, tmp_path: Path) -> None:
    """The regression itself: this raised ValueError and aborted the command."""
    rel_to_root(tmp_path / "anywhere.csv", repo_root)


def test_accepts_str_and_path(repo_root: Path) -> None:
    target = repo_root / "reports" / "x.csv"
    assert rel_to_root(str(target), repo_root) == rel_to_root(target, repo_root)


def test_data_dictionary_is_config_driven(base_config_dict: dict) -> None:
    """The dictionary is an output; it must follow `paths`, not a hardcoded repo location."""
    assert "data_dictionary" in base_config_dict["paths"]
