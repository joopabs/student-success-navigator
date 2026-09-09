"""Raw data loading and schema validation against configs/features.yaml.

Header normalisation: the UCI CSV is semicolon-delimited, UTF-8 with BOM, and one header cell
carries a trailing tab. Names are stripped; source spelling (e.g. "Nacionality") is preserved.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from ssn.config import Config
from ssn.features.allowlist import Allowlist, LeakageError

RAW_SEP = ";"
RAW_ENCODING = "utf-8-sig"


class SchemaError(ValueError):
    """The raw file does not satisfy the documented schema."""


def load_raw(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise SchemaError(
            f"raw dataset not found at {path}. Run `python -m ssn data download` "
            "(or `--from-local <file>`); see data/README.md for provenance."
        )
    df = pd.read_csv(path, sep=RAW_SEP, encoding=RAW_ENCODING)
    df.columns = [str(c).strip() for c in df.columns]
    return df


@dataclass
class ColumnCheck:
    name: str
    availability: str
    role: str
    dtype: str
    pandas_dtype: str
    n_missing: int
    n_unique: int
    documented_codes: int | None
    observed_outside_codes: list[Any] = field(default_factory=list)
    n_outside_codes: int = 0
    range_lo: float | None = None
    range_hi: float | None = None
    n_outside_range: int = 0
    encoding_verified_flag: bool = False
    encoding_check: str = "n/a"  # "match" | "mismatch" | "n/a"


@dataclass
class ValidationReport:
    n_rows: int
    n_cols: int
    columns: list[str]
    target_labels_observed: dict[str, int]
    target_labels_expected: list[str]
    classification_counts: dict[str, int]
    unclassified: list[str]
    classified_but_absent: list[str]
    column_checks: list[ColumnCheck]
    errors: list[str]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, default=str)


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def check_columns(df: pd.DataFrame, allow: Allowlist) -> list[ColumnCheck]:
    checks: list[ColumnCheck] = []
    for name, meta in allow.columns.items():
        if name not in df.columns:
            continue
        s = df[name]
        chk = ColumnCheck(
            name=name,
            availability=meta["availability"],
            role=meta["role"],
            dtype=meta["dtype"],
            pandas_dtype=str(s.dtype),
            n_missing=int(s.isna().sum()),
            n_unique=int(s.nunique(dropna=True)),
            documented_codes=len(meta["codes"]) if meta.get("codes") else None,
            encoding_verified_flag=bool(meta.get("encoding_verified", False)),
        )
        codes = meta.get("codes")
        if codes:
            documented = {int(k) for k in codes}
            observed = set(_numeric(s).dropna().astype(int).unique().tolist())
            outside = sorted(observed - documented)
            chk.observed_outside_codes = outside
            chk.n_outside_codes = int(_numeric(s).isin(outside).sum()) if outside else 0
            chk.encoding_check = "match" if not outside else "mismatch"
        rng = meta.get("range")
        if rng:
            lo, hi = rng
            chk.range_lo, chk.range_hi = lo, hi
            num = _numeric(s)
            chk.n_outside_range = int(((num < lo) | (num > hi)).sum())
        checks.append(chk)
    return checks


def validate(df: pd.DataFrame, cfg: Config, allow: Allowlist) -> ValidationReport:
    errors: list[str] = []
    target_col = cfg.get("data.target_column")
    expected_labels = list(cfg.get("data.target_expected_labels"))

    unclassified = [c for c in df.columns if c not in allow.columns]
    absent = [c for c in allow.columns if c not in df.columns]
    if unclassified:
        errors.append(f"unclassified columns in data: {unclassified}")
    if absent:
        errors.append(f"columns classified in features.yaml but absent from data: {absent}")

    if target_col not in df.columns:
        errors.append(f"target column {target_col!r} not found")
        observed_labels: dict[str, int] = {}
    else:
        observed_labels = {
            str(k): int(v) for k, v in df[target_col].value_counts(dropna=False).items()
        }
        unexpected = sorted(set(observed_labels) - set(expected_labels))
        missing = sorted(set(expected_labels) - set(observed_labels))
        if unexpected or missing:
            errors.append(
                "Target labels differ from documentation: "
                f"unexpected={unexpected} missing={missing}"
            )

    checks = check_columns(df, allow)
    for chk in checks:
        if chk.dtype in {"numeric", "categorical", "binary"} and chk.n_missing == 0:
            if not pd.api.types.is_numeric_dtype(df[chk.name]) and chk.role != "target":
                errors.append(f"{chk.name}: expected numeric storage, got {chk.pandas_dtype}")
        if chk.encoding_verified_flag and chk.encoding_check == "mismatch":
            errors.append(
                f"{chk.name}: marked encoding_verified but observed codes outside documentation: "
                f"{chk.observed_outside_codes}"
            )
        if chk.dtype == "binary" and chk.role != "target":
            vals = set(_numeric(df[chk.name]).dropna().unique().tolist())
            if not vals <= {0, 1}:
                errors.append(f"{chk.name}: binary column has values {sorted(vals)}")

    counts = {
        "allowed": len([c for c in df.columns if c in allow.allowed]),
        "sensitive": len([c for c in df.columns if c in allow.sensitive]),
        "ambiguous": len([c for c in df.columns if c in allow.ambiguous]),
        "second_semester": len(
            [
                c
                for c in df.columns
                if allow.columns.get(c, {}).get("availability") == "second_semester"
            ]
        ),
        "target": int(target_col in df.columns),
        "unclassified": len(unclassified),
    }
    return ValidationReport(
        n_rows=int(len(df)),
        n_cols=int(df.shape[1]),
        columns=list(df.columns),
        target_labels_observed=observed_labels,
        target_labels_expected=expected_labels,
        classification_counts=counts,
        unclassified=unclassified,
        classified_but_absent=absent,
        column_checks=checks,
        errors=errors,
    )


def raise_for_errors(report: ValidationReport) -> None:
    if report.errors:
        leak = [e for e in report.errors if e.startswith("unclassified")]
        msg = "schema validation failed:\n  - " + "\n  - ".join(report.errors)
        raise LeakageError(msg) if leak else SchemaError(msg)
