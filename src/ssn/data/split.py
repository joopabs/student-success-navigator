"""Stratified train/test split, synthetic record ids, demo cohort, evaluator-only labels (T027).

- `is_dropout` = 1 where Target == positive label, else 0 (research R-04).
- `record_id` is a seeded random hex key; row order is shuffled so the id carries no information.
- Demo cohort = test split, record_id + ALLOWED source columns only (no labels, no sensitive
  columns).
- Evaluator file = record_id, is_dropout, Target, sensitive columns, age_band (aggregate audit
  only).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from ssn.config import Config
from ssn.features.allowlist import Allowlist
from ssn.features.engineering import age_band

RECORD_ID = "record_id"
IS_DROPOUT = "is_dropout"
AGE_COL = "Age at enrollment"
AGE_BAND = "age_band"


@dataclass
class SplitOutputs:
    train: pd.DataFrame
    test: pd.DataFrame
    demo: pd.DataFrame
    evaluation: pd.DataFrame
    summary: pd.DataFrame


def derive_target(df: pd.DataFrame, cfg: Config) -> pd.Series:
    col = cfg.get("data.target_column")
    pos = cfg.get("data.target_positive_label")
    return (df[col] == pos).astype(int).rename(IS_DROPOUT)


def synthetic_ids(n: int, seed: int) -> list[str]:
    rng = np.random.default_rng(seed)
    ids: set[str] = set()
    while len(ids) < n:
        ids.add("R" + format(int(rng.integers(0, 16**8)), "08x"))
    return sorted(ids, key=lambda _: rng.random())  # random order, independent of row order


def make_split(df: pd.DataFrame, cfg: Config, allow: Allowlist) -> SplitOutputs:
    seed = cfg.seed
    test_size = float(cfg.get("split.test_size"))
    frame = df.copy()
    frame[IS_DROPOUT] = derive_target(frame, cfg)
    frame = frame.sample(frac=1.0, random_state=seed).reset_index(drop=True)  # shuffle rows
    frame.insert(0, RECORD_ID, synthetic_ids(len(frame), seed))
    bands = cfg.get("fairness.age_bands")
    frame[AGE_BAND] = age_band(frame[AGE_COL], bands) if AGE_COL in frame.columns else pd.NA

    stratify = frame[IS_DROPOUT] if cfg.get("split.stratify") else None
    train, test = train_test_split(frame, test_size=test_size, random_state=seed, stratify=stratify)
    train = train.reset_index(drop=True)
    test = test.reset_index(drop=True)

    demo_cols = [RECORD_ID] + [c for c in df.columns if c in allow.allowed_source]
    demo = test[demo_cols].copy()

    target = cfg.get("data.target_column")
    eval_cols = [RECORD_ID, IS_DROPOUT, target] + sorted(allow.sensitive) + [AGE_BAND]
    evaluation = test[eval_cols].copy()

    summary = pd.DataFrame(
        [
            {
                "split": "train",
                "n": len(train),
                "n_dropout": int(train[IS_DROPOUT].sum()),
                "positive_rate": round(float(train[IS_DROPOUT].mean()), 4),
            },
            {
                "split": "test",
                "n": len(test),
                "n_dropout": int(test[IS_DROPOUT].sum()),
                "positive_rate": round(float(test[IS_DROPOUT].mean()), 4),
            },
            {
                "split": "demo_cohort (=test features only)",
                "n": len(demo),
                "n_dropout": None,
                "positive_rate": None,
            },
        ]
    )
    return SplitOutputs(train=train, test=test, demo=demo, evaluation=evaluation, summary=summary)


def write_outputs(out: SplitOutputs, cfg: Config) -> dict[str, Path]:
    processed = cfg.path_for("processed_dir")
    demo_dir = cfg.path_for("demo_dir")
    eval_dir = cfg.path_for("evaluation_dir")
    tables = cfg.path_for("reports_dir") / "tables"
    for d in (processed, demo_dir, eval_dir, tables):
        d.mkdir(parents=True, exist_ok=True)
    paths = {
        "train": processed / "train.parquet",
        "test": processed / "test.parquet",
        "demo": demo_dir / "demo_cohort.parquet",
        "evaluation": eval_dir / "demo_cohort_labels.parquet",
        "summary": tables / "split_summary.csv",
    }
    out.train.to_parquet(paths["train"], index=False)
    out.test.to_parquet(paths["test"], index=False)
    out.demo.to_parquet(paths["demo"], index=False)
    out.evaluation.to_parquet(paths["evaluation"], index=False)
    out.summary.to_csv(paths["summary"], index=False)
    return paths
