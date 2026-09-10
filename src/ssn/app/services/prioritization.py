"""Ranking, bands, and top-K selection for the Support Queue (deterministic tie-break)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ssn.config import Config
from ssn.modeling.threshold import assign_band

RECORD_ID = "record_id"


def k_options(cfg: Config) -> list[int]:
    per_week = int(cfg.get("capacity.per_week"))
    return [per_week * int(w) for w in cfg.get("capacity.window_sensitivity_weeks")]


def rank_cohort(
    record_ids: pd.Series, scores: np.ndarray, bands: list[dict[str, Any]]
) -> pd.DataFrame:
    """Sort by score desc, then record_id asc (deterministic, documented tie-break)."""
    df = pd.DataFrame({RECORD_ID: record_ids.to_numpy(), "score": np.asarray(scores, dtype=float)})
    df["band"] = [assign_band(s, bands) for s in df["score"]]
    df = df.sort_values(
        ["score", RECORD_ID], ascending=[False, True], kind="mergesort"
    ).reset_index(drop=True)
    df.insert(0, "rank", np.arange(1, len(df) + 1))
    return df


def top_k(ranked: pd.DataFrame, k: int) -> tuple[pd.DataFrame, str | None]:
    n = len(ranked)
    if k > n:
        return (
            ranked.copy(),
            f"Capacity K = {k} exceeds the cohort size ({n}); showing the whole cohort.",
        )
    return ranked.head(int(k)).copy(), None


def band_counts(ranked: pd.DataFrame, bands: list[dict[str, Any]]) -> dict[str, int]:
    counts = ranked["band"].value_counts().to_dict()
    return {b["name"]: int(counts.get(b["name"], 0)) for b in bands}
