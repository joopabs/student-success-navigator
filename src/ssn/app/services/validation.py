"""Server-side validation of the New Record Scoring form against the manifest input schema."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from ssn.explain.language import LanguageRules
from ssn.features.allowlist import Allowlist


@dataclass(frozen=True)
class FieldSpec:
    name: str
    label: str
    kind: str  # numeric | binary | categorical
    options: list[tuple[int, str]] | None  # (code, label) for coded fields
    lo: float | None
    hi: float | None
    availability: str


def build_fields(
    schema: list[dict[str, Any]], allow: Allowlist, rules: LanguageRules
) -> list[FieldSpec]:
    fields = []
    for col in schema:
        name = col["name"]
        meta = allow.columns[name]
        label = rules.features.get(name, {}).get("label", name)
        if col["dtype"] in {"categorical", "binary"} and meta.get("codes"):
            options = [(int(k), str(v)) for k, v in meta["codes"].items()]
            fields.append(
                FieldSpec(name, label, col["dtype"], options, None, None, col["availability"])
            )
        else:
            lo, hi = None, None
            if "documented_range" in col:
                lo, hi = col["documented_range"]
            elif "observed_range_raw" in col:
                lo, hi = col["observed_range_raw"]["min"], col["observed_range_raw"]["max"]
            fields.append(FieldSpec(name, label, "numeric", None, lo, hi, col["availability"]))
    # first-semester fields after enrollment-time fields, for a natural form flow
    return sorted(fields, key=lambda f: (f.availability != "enrollment", f.label))


def validate(
    form: dict[str, Any], fields: list[FieldSpec]
) -> tuple[dict[str, str], pd.DataFrame | None]:
    """Return (errors keyed by field name, one-row DataFrame if valid)."""
    errors: dict[str, str] = {}
    row: dict[str, Any] = {}
    for f in fields:
        raw = form.get(f.name)
        if raw is None or raw == "":
            errors[f.name] = f"{f.label}: a value is required"
            continue
        if f.kind in {"categorical", "binary"}:
            try:
                code = int(raw)
            except (TypeError, ValueError):
                errors[f.name] = f"{f.label}: choose one of the listed options"
                continue
            if f.options is not None and code not in {c for c, _ in f.options}:
                errors[f.name] = f"{f.label}: code {code} is not a documented option"
                continue
            row[f.name] = code
        else:
            try:
                val = float(raw)
            except (TypeError, ValueError):
                errors[f.name] = f"{f.label}: enter a number"
                continue
            if f.lo is not None and val < f.lo or f.hi is not None and val > f.hi:
                errors[f.name] = f"{f.label}: must be between {f.lo:g} and {f.hi:g}"
                continue
            row[f.name] = val
    unexpected = [k for k in form if k not in {f.name for f in fields}]
    if unexpected:
        errors["_form"] = f"unexpected fields are not accepted: {unexpected}"
    if errors:
        return errors, None
    return {}, pd.DataFrame([row])[[f.name for f in fields]]
