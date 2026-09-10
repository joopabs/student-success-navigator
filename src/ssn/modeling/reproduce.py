"""Reproducibility check (T055): compare two runs' report tables and manifests, record deltas."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

COMPARE_TABLES = [
    "cv_comparison.csv",
    "selection_matrix.csv",
    "tuned_params.json",
    "threshold_and_bands.json",
    "calibration_comparison.csv",
    "test_metrics.csv",
    "test_metrics_all_models.csv",
    "test_recall_precision_at_k.csv",
    "selection_cv_by_k.csv",
    "pca_vs_nopca_cv.csv",
]


def _numeric_delta_csv(a: Path, b: Path) -> pd.DataFrame:
    da, db = pd.read_csv(a), pd.read_csv(b)
    rows = []
    common = [
        c
        for c in da.columns
        if c in db.columns
        and pd.api.types.is_numeric_dtype(da[c])
        and pd.api.types.is_numeric_dtype(db[c])
        and "time" not in c.lower()  # wall-clock timings are not reproducible by nature
        and not pd.api.types.is_bool_dtype(da[c])
    ]
    n = min(len(da), len(db))
    for c in common:
        diff = np.abs(da[c].to_numpy(dtype=float)[:n] - db[c].to_numpy(dtype=float)[:n])
        diff = diff[~np.isnan(diff)]
        rows.append(
            {
                "file": a.name,
                "column": c,
                "max_abs_delta": float(diff.max()) if len(diff) else 0.0,
                "rows_compared": int(n),
            }
        )
    if len(da) != len(db):
        rows.append(
            {
                "file": a.name,
                "column": "<row count>",
                "max_abs_delta": float(abs(len(da) - len(db))),
                "rows_compared": n,
            }
        )
    return pd.DataFrame(rows)


def _flatten(d, prefix=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(_flatten(v, f"{prefix}{k}."))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out.update(_flatten(v, f"{prefix}{i}."))
    elif isinstance(d, (int, float)) and not isinstance(d, bool):
        out[prefix.rstrip(".")] = float(d)
    return out


def _numeric_delta_json(a: Path, b: Path) -> pd.DataFrame:
    fa, fb = _flatten(json.loads(a.read_text())), _flatten(json.loads(b.read_text()))
    rows = [
        {"file": a.name, "column": k, "max_abs_delta": abs(fa[k] - fb[k]), "rows_compared": 1}
        for k in fa
        if k in fb
    ]
    return pd.DataFrame(rows)


def compare_runs(tables_a: Path, tables_b: Path) -> pd.DataFrame:
    frames = []
    for name in COMPARE_TABLES:
        a, b = tables_a / name, tables_b / name
        if not (a.is_file() and b.is_file()):
            continue
        frames.append(
            _numeric_delta_json(a, b) if name.endswith(".json") else _numeric_delta_csv(a, b)
        )
    return (
        pd.concat(frames, ignore_index=True)
        if frames
        else pd.DataFrame(columns=["file", "column", "max_abs_delta", "rows_compared"])
    )


def write_report(
    deltas: pd.DataFrame, tolerance: float, out_path: Path, run_a: str, run_b: str
) -> bool:
    worst = deltas.sort_values("max_abs_delta", ascending=False)
    ok = bool((deltas["max_abs_delta"] <= tolerance).all()) if len(deltas) else True
    per_file = deltas.groupby("file")["max_abs_delta"].max().reset_index()
    lines = [
        "# Reproducibility",
        "",
        f"**Checked:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')} "
        "by `python -m ssn reproduce-check`.",
        f"**Run A:** `{run_a}` · **Run B:** `{run_b}` · "
        f"**Tolerance (max absolute delta):** {tolerance}",
        f"**Result:** {'PASS' if ok else 'FAIL'} — largest observed delta "
        f"{worst['max_abs_delta'].max() if len(worst) else 0.0:.3g}",
        "",
        "Both runs use the single seed in `configs/base.yaml`, config-driven commands, and "
        "`n_jobs=1` for the final fit.",
        "Residual nondeterminism, if any, comes from parallel RandomizedSearchCV scheduling "
        "(results are seeded) and BLAS.",
        "",
        "## Largest delta per file",
        "",
        "| file | max abs delta |",
        "|---|---|",
        *[f"| {r.file} | {r.max_abs_delta:.3g} |" for r in per_file.itertuples()],
        "",
        "## Top 15 deltas",
        "",
        "| file | column | max abs delta |",
        "|---|---|---|",
        *[
            f"| {r.file} | {r.column} | {r.max_abs_delta:.3g} |"
            for r in worst.head(15).itertuples()
        ],
        "",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    return ok
