"""Read precomputed fairness results for the Equity Dashboard. Computes nothing."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import pandas as pd

from ssn.config import Config


def load_equity(cfg: Config) -> dict[str, Any] | None:
    fa = cfg.path_for("reports_dir") / "fairness"
    p = fa / "group_metrics.json"
    if not p.is_file():
        return None
    payload = json.loads(p.read_text())
    mit = fa / "mitigation_comparison.csv"
    payload["mitigation"] = pd.read_csv(mit).to_dict(orient="records") if mit.is_file() else []
    payload["figures"] = {
        name: _b64(fa / f"{name}.png") for name in ("selection_rates", "group_calibration")
    }
    return payload


def _b64(path: Path) -> str | None:
    if not path.is_file():
        return None
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()
