"""Candidate pipeline builder (T043): preprocess -> [selector] -> [PCA] -> [SMOTENC] -> estimator.

Everything is a pipeline step, so under cross-validation each is fitted on training folds only.
SMOTENC (imbalanced-learn) runs after preprocessing; the categorical mask is derived from the
deterministic ColumnTransformer layout (numeric block first, then binary + one-hot) at fit time.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

import numpy as np
from imblearn.base import BaseSampler
from imblearn.over_sampling import SMOTENC
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline

from ssn.config import Config, ModelConfig, load_model_config
from ssn.features.allowlist import Allowlist
from ssn.features.preprocess import build_preprocessor, feature_groups
from ssn.modeling.selection import make_embedded, make_filter

CANDIDATES = ["dummy", "logreg", "random_forest", "hist_gb"]


class SMOTENCAfterPreprocess(BaseSampler):
    """SMOTENC whose categorical mask is 'every column after the numeric block'."""

    _sampling_type = "over-sampling"
    _parameter_constraints: dict = {}

    def __init__(self, n_numeric: int, random_state: int | None = None, k_neighbors: int = 5):
        super().__init__()
        self.n_numeric = n_numeric
        self.random_state = random_state
        self.k_neighbors = k_neighbors

    def _fit_resample(self, X, y):
        X = np.asarray(X)
        cat_idx = [int(i) for i in range(self.n_numeric, X.shape[1])]  # indices, not a bool mask
        sampler = SMOTENC(
            categorical_features=cat_idx,
            random_state=self.random_state,
            k_neighbors=self.k_neighbors,
        )
        return sampler.fit_resample(X, y)


def _import_estimator(path: str):
    module, cls = path.rsplit(".", 1)
    return getattr(importlib.import_module(module), cls)


@dataclass(frozen=True)
class SelectionSetting:
    kind: str  # filter | embedded
    method: str
    k: int | str


def estimator_from(mc: ModelConfig):
    return _import_estimator(mc.estimator)(**mc.params)


def build_pipeline(
    name: str,
    cfg: Config,
    allow: Allowlist,
    *,
    selection: SelectionSetting | None = None,
    smote: bool = False,
    use_pca: bool | None = None,
    params_override: dict[str, Any] | None = None,
) -> Pipeline:
    """Build a candidate from configs/models/<name>.yaml.

    `selection` is applied only when the model config sets `use_selection: true` and a setting is
    given (from reports/tables/selection_decision.json). `smote` inserts SMOTENC after selection.
    """
    mc = load_model_config(name, cfg)
    params = dict(mc.params)
    params.update(params_override or {})
    est = _import_estimator(mc.estimator)(**params)
    pca = mc.use_pca if use_pca is None else use_pca
    steps: list[tuple[str, Any]] = [("pre", build_preprocessor(allow, scale_numeric=True))]
    if mc.use_selection and selection is not None:
        sel = (
            make_filter(selection.method, selection.k, cfg.seed)
            if selection.kind == "filter"
            else make_embedded(selection.method, selection.k, cfg.seed)
        )
        steps.append(("select", sel))
    if pca:
        steps.append(
            (
                "pca",
                PCA(n_components=float(cfg.get("pca.variance_threshold")), random_state=cfg.seed),
            )
        )
    if smote:
        n_numeric = len(feature_groups(allow)["numeric"])
        steps.append(("smote", SMOTENCAfterPreprocess(n_numeric=n_numeric, random_state=cfg.seed)))
        steps.append(("clf", est))
        return ImbPipeline(steps)
    steps.append(("clf", est))
    return Pipeline(steps)


def describe(pipeline: Pipeline, name: str, mc: ModelConfig) -> dict[str, Any]:
    clf = pipeline.named_steps["clf"]
    keys = (
        "class_weight",
        "C",
        "n_estimators",
        "max_depth",
        "learning_rate",
        "max_leaf_nodes",
        "strategy",
    )
    params = {k: v for k, v in clf.get_params(deep=False).items() if k in keys and v is not None}
    return {
        "model": name,
        "estimator": mc.estimator,
        "key_params": ";".join(f"{k}={v}" for k, v in params.items()),
        "steps": ">".join(s for s, _ in pipeline.steps),
    }
