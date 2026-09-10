"""Load the persisted artifact and score frames. NEVER fits or retrains (tested by AST scan)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ssn.config import Config
from ssn.features import allowlist as al
from ssn.features.allowlist import Allowlist
from ssn.features.preprocess import project_for_model
from ssn.modeling.persist import ArtifactError, load_artifact


@dataclass
class ArtifactBundle:
    manifest: dict[str, Any]
    pipeline: Any
    allow: Allowlist
    threshold: float
    bands: list[dict[str, Any]]
    model_version: str
    schema: list[dict[str, Any]] = field(default_factory=list)


def load_bundle(cfg: Config) -> ArtifactBundle:
    """Verified load: version must match config, pipeline sha256 must match the manifest."""
    manifest, pipeline = load_artifact(
        cfg.path_for("models_dir"), expected_version=str(cfg.get("app.expected_model_version"))
    )
    allow = al.load(cfg.path_for("features_yaml"))
    return ArtifactBundle(
        manifest=manifest,
        pipeline=pipeline,
        allow=allow,
        threshold=float(manifest["threshold"]["value"]),
        bands=list(manifest["bands"]),
        model_version=str(manifest["model_version"]),
        schema=list(manifest["features"]["input_schema"]),
    )


def score_frame(bundle: ArtifactBundle, df: pd.DataFrame) -> np.ndarray:
    """Project to allow-listed inputs, assert the leakage guard, predict. No fitting."""
    X = project_for_model(df, bundle.allow)
    bundle.allow.assert_frame_allowed(X)
    return bundle.pipeline.predict_proba(X)[:, 1]


def load_reference_medians(cfg: Config) -> dict[str, float]:
    p = cfg.path_for("reports_dir") / "explainability" / "reference_medians_train.json"
    return json.loads(p.read_text()) if p.is_file() else {}


__all__ = [
    "ArtifactBundle",
    "ArtifactError",
    "load_bundle",
    "score_frame",
    "load_reference_medians",
    "Path",
]
