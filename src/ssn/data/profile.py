"""Profiling of the raw dataset: per-column statistics, target balance, duplicates, invalid
values, outlier candidates, categorical code coverage, and observed ranges for app validation.

Nothing here splits, imputes, scales, or engineers features. `is_dropout` appears only as a
derived summary of the Target distribution (PROJECT_DECISIONS: Dropout=1, else 0).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ssn.config import Config
from ssn.features.allowlist import Allowlist


@dataclass
class ProfileOutputs:
    columns: pd.DataFrame
    target: pd.DataFrame
    duplicates: pd.DataFrame
    categorical_values: pd.DataFrame
    invalid_values: pd.DataFrame
    outliers: pd.DataFrame
    ranges: dict[str, dict[str, float]]


def profile_columns(df: pd.DataFrame, allow: Allowlist) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        meta = allow.columns.get(col, {})
        s = df[col]
        num = pd.to_numeric(s, errors="coerce") if meta.get("role") != "target" else None
        rows.append(
            {
                "column": col,
                "availability": meta.get("availability", "unclassified"),
                "role": meta.get("role", "unclassified"),
                "dtype": meta.get("dtype", "unknown"),
                "pandas_dtype": str(s.dtype),
                "n_missing": int(s.isna().sum()),
                "pct_missing": round(100 * s.isna().mean(), 3),
                "n_unique": int(s.nunique(dropna=True)),
                "min": None if num is None else num.min(),
                "p50": None if num is None else num.median(),
                "max": None if num is None else num.max(),
                "mean": None if num is None else round(float(num.mean()), 4),
                "std": None if num is None else round(float(num.std()), 4),
                "n_documented_codes": len(meta["codes"]) if meta.get("codes") else None,
                "encoding_verified": meta.get("encoding_verified"),
            }
        )
    return pd.DataFrame(rows)


def profile_target(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    col = cfg.get("data.target_column")
    pos = cfg.get("data.target_positive_label")
    counts = df[col].value_counts(dropna=False)
    out = pd.DataFrame({"label": counts.index.astype(str), "count": counts.values})
    out["share"] = (out["count"] / out["count"].sum()).round(4)
    out["is_dropout"] = (out["label"] == pos).astype(int)
    binary = out.groupby("is_dropout")["count"].sum()
    out.attrs["is_dropout_positive_rate"] = round(float(binary.get(1, 0) / binary.sum()), 4)
    return out


def profile_duplicates(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    target = cfg.get("data.target_column")
    feats = [c for c in df.columns if c != target]
    return pd.DataFrame(
        [
            {"rule": "exact duplicate rows (all columns)", "count": int(df.duplicated().sum())},
            {
                "rule": "duplicate feature rows ignoring Target",
                "count": int(df.duplicated(subset=feats).sum()),
            },
            {
                "rule": "duplicate feature rows with conflicting Target",
                "count": int(
                    df[df.duplicated(subset=feats, keep=False)]
                    .groupby(feats, dropna=False)[target]
                    .nunique()
                    .gt(1)
                    .sum()
                ),
            },
        ]
    )


def profile_categorical_values(df: pd.DataFrame, allow: Allowlist) -> pd.DataFrame:
    rows = []
    for col, meta in allow.columns.items():
        if col not in df.columns or meta.get("dtype") not in {"categorical", "binary"}:
            continue
        codes = {int(k): v for k, v in (meta.get("codes") or {}).items()}
        counts = pd.to_numeric(df[col], errors="coerce").value_counts(dropna=False)
        for code, n in counts.items():
            code_int = int(code) if pd.notna(code) else None
            rows.append(
                {
                    "column": col,
                    "code": code_int,
                    "label": codes.get(code_int, "") if code_int is not None else "<missing>",
                    "count": int(n),
                    "documented": code_int in codes if codes else None,
                }
            )
    return pd.DataFrame(rows).sort_values(["column", "count"], ascending=[True, False])


def profile_invalid_values(df: pd.DataFrame, allow: Allowlist) -> pd.DataFrame:
    rows = []
    for col, meta in allow.columns.items():
        if col not in df.columns or meta.get("role") == "target":
            continue
        num = pd.to_numeric(df[col], errors="coerce")
        rows.append(
            {"column": col, "rule": "non-numeric or missing", "count": int(num.isna().sum())}
        )
        if meta.get("codes"):
            documented = {int(k) for k in meta["codes"]}
            rows.append(
                {
                    "column": col,
                    "rule": "code not in UCI documentation",
                    "count": int((~num.dropna().astype(int).isin(documented)).sum()),
                }
            )
        if meta.get("range"):
            lo, hi = meta["range"]
            rows.append(
                {
                    "column": col,
                    "rule": f"outside documented range [{lo}, {hi}]",
                    "count": int(((num < lo) | (num > hi)).sum()),
                }
            )
        if (
            meta.get("dtype") == "numeric"
            and meta.get("nonnegative", True)
            and not meta.get("range")
        ):
            rows.append({"column": col, "rule": "negative value", "count": int((num < 0).sum())})
    return pd.DataFrame(rows)


def profile_outliers(df: pd.DataFrame, allow: Allowlist, k: float = 1.5) -> pd.DataFrame:
    rows = []
    for col, meta in allow.columns.items():
        if col not in df.columns or meta.get("dtype") != "numeric":
            continue
        num = pd.to_numeric(df[col], errors="coerce").dropna()
        q1, q3 = num.quantile(0.25), num.quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - k * iqr, q3 + k * iqr
        rows.append(
            {
                "column": col,
                "q1": q1,
                "q3": q3,
                "iqr_low_fence": lo,
                "iqr_high_fence": hi,
                "n_below": int((num < lo).sum()),
                "n_above": int((num > hi).sum()),
                "n_zero": int((num == 0).sum()),
            }
        )
    return pd.DataFrame(rows)


def observed_ranges(df: pd.DataFrame, allow: Allowlist) -> dict[str, dict[str, float]]:
    out = {}
    for col, meta in allow.columns.items():
        if col in df.columns and meta.get("dtype") == "numeric":
            num = pd.to_numeric(df[col], errors="coerce")
            out[col] = {"min": float(num.min()), "max": float(num.max())}
    return out


def run_profile(df: pd.DataFrame, cfg: Config, allow: Allowlist) -> ProfileOutputs:
    return ProfileOutputs(
        columns=profile_columns(df, allow),
        target=profile_target(df, cfg),
        duplicates=profile_duplicates(df, cfg),
        categorical_values=profile_categorical_values(df, allow),
        invalid_values=profile_invalid_values(df, allow),
        outliers=profile_outliers(df, allow),
        ranges=observed_ranges(df, allow),
    )


def write_outputs(out: ProfileOutputs, tables_dir: Path, ranges_path: Path) -> list[Path]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, frame in [
        ("profile_columns", out.columns),
        ("profile_target", out.target),
        ("profile_duplicates", out.duplicates),
        ("profile_categorical_values", out.categorical_values),
        ("profile_invalid_values", out.invalid_values),
        ("profile_outliers", out.outliers),
    ]:
        p = tables_dir / f"{name}.csv"
        frame.to_csv(p, index=False)
        written.append(p)
    ranges_path.write_text(json.dumps(out.ranges, indent=2, default=float) + "\n")
    written.append(ranges_path)
    return written
