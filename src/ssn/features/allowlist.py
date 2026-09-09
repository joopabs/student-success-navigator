"""Feature allow-list enforcement (constitution Principle V, gate G3).

Contract: specs/001-dropout-risk-navigator/contracts/feature-allowlist.md
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

AVAILABILITY = {"enrollment", "first_semester", "second_semester", "outcome", "ambiguous"}
ROLES = {"feature", "sensitive", "target", "id", "excluded"}
DTYPES = {"numeric", "categorical", "binary"}
ALLOWED_AVAILABILITY = {"enrollment", "first_semester"}


class LeakageError(RuntimeError):
    """A column that is not allow-listed reached (or would reach) the model."""


class AllowlistConfigError(ValueError):
    """configs/features.yaml is malformed."""


@dataclass(frozen=True)
class Allowlist:
    columns: dict[str, dict[str, Any]]
    engineered: dict[str, dict[str, Any]]
    allowed: frozenset[str]
    prohibited: frozenset[str]
    sensitive: frozenset[str]
    ambiguous: frozenset[str]
    target: str | None
    source: Path | None = None
    _visible: frozenset[str] = field(default_factory=frozenset, repr=False)

    @property
    def allowed_source(self) -> frozenset[str]:
        return frozenset(c for c in self.allowed if c in self.columns)

    @property
    def allowed_engineered(self) -> frozenset[str]:
        return frozenset(c for c in self.allowed if c in self.engineered)

    @property
    def adviser_visible(self) -> frozenset[str]:
        return self._visible

    def classify(self, column: str) -> str:
        """Return 'allowed', 'prohibited', 'sensitive', 'target', or 'unclassified'."""
        if column in self.allowed:
            return "allowed"
        if column in self.sensitive:
            return "sensitive"
        if column == self.target:
            return "target"
        if column in self.prohibited:
            return "prohibited"
        return "unclassified"

    def assert_all_classified(self, raw_columns: Iterable[str]) -> None:
        """Every raw column must appear exactly once in features.yaml."""
        raw = list(raw_columns)
        unclassified = [c for c in raw if c not in self.columns]
        missing = [c for c in self.columns if c not in raw]
        if unclassified or missing:
            raise LeakageError(
                "configs/features.yaml does not match the data. "
                f"Unclassified columns: {unclassified}. Classified but absent: {missing}."
            )

    def project_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return only allow-listed columns present in df (source and engineered)."""
        keep = [c for c in df.columns if c in self.allowed]
        return df.loc[:, keep]

    def assert_frame_allowed(self, X: pd.DataFrame) -> None:
        """Raise LeakageError naming any column of X that is not allow-listed."""
        offending = [c for c in X.columns if c not in self.allowed]
        if offending:
            detail = {c: self.classify(c) for c in offending}
            raise LeakageError(f"non-allow-listed columns reached the model: {detail}")


def _validate_entry(entry: dict[str, Any], idx: int) -> None:
    for key in ("name", "availability", "role", "dtype", "adviser_visible"):
        if key not in entry:
            raise AllowlistConfigError(f"columns[{idx}]: missing key {key!r}")
    if entry["availability"] not in AVAILABILITY:
        raise AllowlistConfigError(f"{entry['name']}: bad availability {entry['availability']!r}")
    if entry["role"] not in ROLES:
        raise AllowlistConfigError(f"{entry['name']}: bad role {entry['role']!r}")
    if entry["dtype"] not in DTYPES:
        raise AllowlistConfigError(f"{entry['name']}: bad dtype {entry['dtype']!r}")
    if entry["role"] == "sensitive" and entry["adviser_visible"]:
        raise AllowlistConfigError(f"{entry['name']}: sensitive columns cannot be adviser_visible")


def build(raw: dict[str, Any], source: Path | None = None) -> Allowlist:
    columns_list = raw.get("columns") or []
    engineered_list = raw.get("engineered") or []
    columns: dict[str, dict[str, Any]] = {}
    for i, entry in enumerate(columns_list):
        _validate_entry(entry, i)
        if entry["name"] in columns:
            raise AllowlistConfigError(f"duplicate column entry: {entry['name']!r}")
        columns[entry["name"]] = entry

    targets = [n for n, e in columns.items() if e["role"] == "target"]
    if len(targets) > 1:
        raise AllowlistConfigError(f"exactly one target column allowed, got {targets}")
    target = targets[0] if targets else None

    allowed = {
        n
        for n, e in columns.items()
        if e["role"] == "feature" and e["availability"] in ALLOWED_AVAILABILITY
    }
    sensitive = {n for n, e in columns.items() if e["role"] == "sensitive"}
    ambiguous = {n for n, e in columns.items() if e["availability"] == "ambiguous"}

    engineered: dict[str, dict[str, Any]] = {}
    for i, entry in enumerate(engineered_list):
        for key in ("name", "inputs", "adviser_visible"):
            if key not in entry:
                raise AllowlistConfigError(f"engineered[{i}]: missing key {key!r}")
        bad_inputs = [c for c in entry["inputs"] if c not in allowed]
        if bad_inputs and not entry.get("audit_only", False):
            raise AllowlistConfigError(
                f"engineered feature {entry['name']!r} uses non-allow-listed inputs {bad_inputs}"
            )
        engineered[entry["name"]] = entry
        if not entry.get("audit_only", False):
            allowed.add(entry["name"])

    prohibited = (set(columns) | set(engineered)) - allowed
    visible = {n for n, e in {**columns, **engineered}.items() if e.get("adviser_visible")}
    return Allowlist(
        columns=columns,
        engineered=engineered,
        allowed=frozenset(allowed),
        prohibited=frozenset(prohibited),
        sensitive=frozenset(sensitive),
        ambiguous=frozenset(ambiguous),
        target=target,
        source=source,
        _visible=frozenset(visible),
    )


def load(path: str | Path = "configs/features.yaml") -> Allowlist:
    p = Path(path)
    raw = yaml.safe_load(p.read_text()) or {}
    return build(raw, source=p)


# Module-level conveniences used by the contract text and tests.
def project_features(df: pd.DataFrame, allowlist: Allowlist) -> pd.DataFrame:
    return allowlist.project_features(df)


def assert_frame_allowed(X: pd.DataFrame, allowlist: Allowlist) -> None:
    allowlist.assert_frame_allowed(X)
