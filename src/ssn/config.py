"""Configuration loading and validation.

Contract: specs/001-dropout-risk-navigator/contracts/config-schema.md
Constitution IV: one seed, config-driven runs, no hard-coded hyperparameters.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from ssn.paths import repo_root, resolve


class ConfigError(ValueError):
    """Raised when a configuration file is missing keys or has wrong types."""


# key path -> expected type(s). Lists give (container type, element type).
REQUIRED: dict[str, Any] = {
    "project.name": str,
    "project.model_version": str,
    "seed": int,
    "paths.raw_csv": str,
    "paths.interim_dir": str,
    "paths.processed_dir": str,
    "paths.demo_dir": str,
    "paths.evaluation_dir": str,
    "paths.local_dir": str,
    "paths.models_dir": str,
    "paths.reports_dir": str,
    "paths.features_yaml": str,
    "paths.language_yaml": str,
    "data.expected_sha256": str,
    "data.target_column": str,
    "data.target_positive_label": str,
    "data.target_expected_labels": (list, str),
    "split.test_size": float,
    "split.stratify": bool,
    "split.cv_folds": int,
    "capacity.per_week": int,
    "capacity.window_weeks": int,
    "capacity.k": int,
    "capacity.window_sensitivity_weeks": (list, int),
    "capacity.illustrative": bool,
    "threshold.rule": str,
    "threshold.band_names": (list, str),
    "threshold.middle_band_selection_rate_multiplier": float,
    "imbalance.primary": str,
    "imbalance.compare_smote": bool,
    "selection.filter_method": str,
    "selection.embedded_method": str,
    "selection.k_grid": (list, object),
    "pca.variance_threshold": float,
    "pca.compare_in_cv": bool,
    "fairness.attributes": (list, str),
    "fairness.min_group_size": int,
    "fairness.reference_group": str,
    "fairness.age_bands": (list, object),
    "explain.method": str,
    "explain.pdp_min_distinct_values": int,
    "app.host": str,
    "app.port": int,
    "app.expected_model_version": str,
    "app.actions_db": str,
    "app.disclaimer_key": str,
    "report.reproduction_tolerance_file": str,
}

ENUMS: dict[str, set[str]] = {
    "threshold.rule": {"oof_quantile_for_capacity"},
    "imbalance.primary": {"class_weight", "smote"},
    "selection.filter_method": {"mutual_info", "anova_f"},
    "selection.embedded_method": {"l1_logreg", "tree_importance"},
    "fairness.reference_group": {"largest"},
    "explain.method": {"shap", "permutation"},
}


def _get(d: dict[str, Any], dotted: str) -> Any:
    cur: Any = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(dotted)
        cur = cur[part]
    return cur


def _check_type(dotted: str, value: Any, expected: Any) -> None:
    if isinstance(expected, tuple):
        container, elem = expected
        if not isinstance(value, container):
            raise ConfigError(
                f"{dotted}: expected {container.__name__}, got {type(value).__name__}"
            )
        if elem is not object:
            bad = [
                v for v in value if not isinstance(v, elem) or isinstance(v, bool) and elem is int
            ]
            if bad:
                raise ConfigError(f"{dotted}: all items must be {elem.__name__}, got {bad!r}")
        return
    if expected is float and isinstance(value, int) and not isinstance(value, bool):
        return  # allow 1 for 1.0
    if expected is int and isinstance(value, bool):
        raise ConfigError(f"{dotted}: expected int, got bool")
    if not isinstance(value, expected):
        raise ConfigError(f"{dotted}: expected {expected.__name__}, got {type(value).__name__}")


def validate_raw(raw: dict[str, Any]) -> None:
    """Validate a parsed YAML mapping against the contract. Raises ConfigError."""
    if not isinstance(raw, dict):
        raise ConfigError("top level: expected a mapping")
    for dotted, expected in REQUIRED.items():
        try:
            value = _get(raw, dotted)
        except KeyError:
            raise ConfigError(f"missing required key: {dotted}") from None
        _check_type(dotted, value, expected)
    for dotted, allowed in ENUMS.items():
        value = _get(raw, dotted)
        if value not in allowed:
            raise ConfigError(f"{dotted}: {value!r} not in {sorted(allowed)}")
    cap = raw["capacity"]
    if cap["illustrative"] is not True:
        raise ConfigError(
            "capacity.illustrative: must be true (all capacity values are assumptions)"
        )
    if cap["k"] != cap["per_week"] * cap["window_weeks"]:
        raise ConfigError(
            f"capacity.k ({cap['k']}) must equal per_week * window_weeks "
            f"({cap['per_week']} * {cap['window_weeks']})"
        )
    if not 0.0 < raw["split"]["test_size"] < 1.0:
        raise ConfigError("split.test_size: must be between 0 and 1")
    if raw["split"]["cv_folds"] < 2:
        raise ConfigError("split.cv_folds: must be at least 2")
    if len(raw["threshold"]["band_names"]) != 3:
        raise ConfigError("threshold.band_names: exactly three supportive band names are required")
    data = raw["data"]
    if data["target_positive_label"] not in data["target_expected_labels"]:
        raise ConfigError("data.target_positive_label must be one of data.target_expected_labels")
    if raw["project"]["model_version"] != raw["app"]["expected_model_version"]:
        raise ConfigError("project.model_version must equal app.expected_model_version")


@dataclass(frozen=True)
class Config:
    """Validated, immutable view of configs/base.yaml."""

    raw: dict[str, Any]
    path: Path
    root: Path

    @property
    def seed(self) -> int:
        return int(self.raw["seed"])

    def get(self, dotted: str) -> Any:
        return _get(self.raw, dotted)

    def path_for(self, key: str) -> Path:
        """Resolve `paths.<key>` (or `app.actions_db`) against the repository root."""
        dotted = key if "." in key else f"paths.{key}"
        return resolve(str(self.get(dotted)), self.root)

    @property
    def capacity_k_values(self) -> list[int]:
        cap = self.raw["capacity"]
        return [cap["per_week"] * w for w in cap["window_sensitivity_weeks"]]


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def load(path: str | Path = "configs/base.yaml", *, set_seeds: bool = True) -> Config:
    """Load and validate base.yaml; seed `random` and `numpy`; return a frozen Config."""
    root = repo_root()
    cfg_path = resolve(path, root)
    if not cfg_path.is_file():
        raise ConfigError(f"config file not found: {cfg_path}")
    with cfg_path.open() as fh:
        raw = yaml.safe_load(fh) or {}
    validate_raw(raw)
    if set_seeds:
        seed_everything(int(raw["seed"]))
    return Config(raw=raw, path=cfg_path, root=root)


def _substitute(obj: Any, mapping: dict[str, Any]) -> Any:
    if isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        key = obj[2:-1]
        if key not in mapping:
            raise ConfigError(f"unknown substitution ${{{key}}}")
        return mapping[key]
    if isinstance(obj, dict):
        return {k: _substitute(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_substitute(v, mapping) for v in obj]
    return obj


MODEL_REQUIRED = {
    "name": str,
    "estimator": str,
    "params": dict,
    "search_space": dict,
    "n_iter": int,
    "use_selection": bool,
    "use_pca": bool,
}


@dataclass(frozen=True)
class ModelConfig:
    name: str
    estimator: str
    params: dict[str, Any]
    search_space: dict[str, Any]
    n_iter: int
    use_selection: bool
    use_pca: bool
    extra: dict[str, Any] = field(default_factory=dict)


def load_model_config(
    name: str, cfg: Config, models_dir: str | Path = "configs/models"
) -> ModelConfig:
    """Load configs/models/<name>.yaml, substituting ${seed} from the base config."""
    path = resolve(Path(models_dir) / f"{name}.yaml", cfg.root)
    if not path.is_file():
        raise ConfigError(f"model config not found: {path}")
    raw = yaml.safe_load(path.read_text()) or {}
    for key, typ in MODEL_REQUIRED.items():
        if key not in raw:
            raise ConfigError(f"{path.name}: missing required key: {key}")
        if not isinstance(raw[key], typ) or (typ is int and isinstance(raw[key], bool)):
            raise ConfigError(f"{path.name}: {key}: expected {typ.__name__}")
    if raw["name"] != name:
        raise ConfigError(f"{path.name}: name {raw['name']!r} does not match file name {name!r}")
    raw = _substitute(raw, {"seed": cfg.seed})
    known = set(MODEL_REQUIRED)
    return ModelConfig(
        **{k: raw[k] for k in known}, extra={k: v for k, v in raw.items() if k not in known}
    )
