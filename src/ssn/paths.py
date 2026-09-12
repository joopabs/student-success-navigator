"""Repository path helpers."""

from __future__ import annotations

from pathlib import Path


def repo_root(start: Path | None = None) -> Path:
    """Return the repository root: the nearest ancestor containing pyproject.toml."""
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return here


def rel_to_root(path: str | Path, root: Path | None = None) -> str:
    """Repo-relative path for display, falling back to the absolute path.

    Output directories are config-driven and may legitimately sit outside the repository — a second
    pipeline run for `reproduce-check`, or a pytest tmp_path. `Path.relative_to` raises `ValueError`
    in that case, which previously aborted commands *after* they had already written their files.
    """
    p = Path(path)
    try:
        return str(p.relative_to(root or repo_root()))
    except ValueError:
        return str(p)


def resolve(path: str | Path, root: Path | None = None) -> Path:
    """Resolve a config-relative path against the repository root."""
    p = Path(path)
    return p if p.is_absolute() else (root or repo_root()) / p
