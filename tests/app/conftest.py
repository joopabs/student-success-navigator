"""Fixture AppState built from synthetic rows and a small fitted pipeline (fitted HERE, in tests,
never in app code). No real student data, no real artifact needed, so these tests run in CI."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
from plotly.utils import PlotlyJSONEncoder

from ssn.app.services.action_log import ActionLog
from ssn.app.services.explanations import PrecomputedShap
from ssn.app.services.inference import ArtifactBundle, score_frame
from ssn.app.services.prioritization import k_options, rank_cohort
from ssn.app.services.validation import build_fields
from ssn.app.state import DISCLAIMER, AppState
from ssn.config import load
from ssn.explain import language as L
from ssn.features import allowlist as al
from ssn.features.engineering import ENGINEERED_NAMES
from ssn.features.preprocess import project_for_model
from ssn.modeling.candidates import build_pipeline

BANDS = [
    {"name": "Priority outreach", "lower": 0.7, "upper": 1.0, "rule": "top"},
    {"name": "Check-in suggested", "lower": 0.5, "upper": 0.7, "rule": "mid"},
    {"name": "Standard support", "lower": 0.0, "upper": 0.5, "rule": "rest"},
]


def _schema(allow):
    out = []
    for name in sorted(allow.allowed_source):
        meta = allow.columns[name]
        e = {"name": name, "dtype": meta["dtype"], "availability": meta["availability"]}
        if meta.get("codes"):
            e["allowed_codes"] = [int(k) for k in meta["codes"]]
        elif meta.get("range"):
            e["documented_range"] = list(meta["range"])
        else:
            e["observed_range_raw"] = {"min": 0.0, "max": 20.0}
        out.append(e)
    return out


@pytest.fixture(scope="session")
def fixture_state(real_named_frame, tmp_path_factory):
    cfg = load("configs/base.yaml", set_seeds=False)
    allow = al.load("configs/features.yaml")
    rules = L.load("configs/language.yaml")
    train = real_named_frame.copy()
    X = project_for_model(train, allow)
    pipe = build_pipeline("logreg", cfg, allow).fit(
        X, train["is_dropout"]
    )  # fitted in the TEST only
    manifest = {
        "model_version": cfg.get("project.model_version"),
        "created_at": "2026-09-10T00:00:00Z",
        "pipeline_sha256": "f" * 64,
        "estimator": {"class": "sklearn.linear_model.LogisticRegression"},
        "calibration": {"applied": False, "method": None},
        "bands": BANDS,
        "threshold": {"value": 0.7, "capacity_k": 50, "n_cohort_expected": 885},
        "intended_use": "Decision support for voluntary outreach.",
        "non_use": "No adverse decisions.",
        "test_summary": {
            "pr_auc": 0.5,
            "roc_auc": 0.5,
            "recall_at_k": 0.1,
            "precision_at_k": 0.5,
            "brier": 0.2,
            "ece": 0.05,
            "k_applied_to_test": 50,
        },
        "cv_summary": {"pr_auc": 0.5, "pr_auc_std_cv": 0.01},
        "test_evaluations": 1,
        "measured_vs_illustrative": "measured vs illustrative",
        "features": {"input_schema": _schema(allow)},
    }
    bundle = ArtifactBundle(
        manifest=manifest,
        pipeline=pipe,
        allow=allow,
        threshold=0.7,
        bands=BANDS,
        model_version=str(cfg.get("project.model_version")),
        schema=manifest["features"]["input_schema"],
    )
    cohort = X.copy()
    cohort.insert(0, "record_id", [f"R{i:08x}" for i in range(len(cohort))])
    scores = score_frame(bundle, cohort)
    ranked = rank_cohort(cohort["record_id"], scores, BANDS)
    rng = np.random.default_rng(0)
    feats = sorted(allow.allowed_source) + list(ENGINEERED_NAMES)
    shap = PrecomputedShap(
        rng.normal(0, 0.05, size=(len(cohort), len(feats))), feats, list(cohort["record_id"]), 0.5
    )
    tmp = tmp_path_factory.mktemp("app")
    equity = {
        "cohort": "fixture",
        "n": len(cohort),
        "threshold": 0.7,
        "k": 20,
        "min_group_size": 30,
        "attributes": ["gender", "age_band"],
        "gender_encoding": {1: "male", 0: "female"},
        "gender_encoding_verified": True,
        "groups": [
            {
                "attribute": "gender",
                "operating_point": "threshold",
                "group": "female",
                "n": 150,
                "reliable": True,
                "base_rate": 0.3,
                "selection_rate": 0.05,
                "tpr": 0.2,
                "fpr": 0.01,
                "brier": 0.1,
            },
            {
                "attribute": "gender",
                "operating_point": "top_k=20",
                "group": "female",
                "n": 150,
                "reliable": True,
                "base_rate": 0.3,
                "selection_rate": 0.05,
                "tpr": 0.2,
                "fpr": 0.01,
                "brier": 0.1,
            },
            {
                "attribute": "age_band",
                "operating_point": "threshold",
                "group": "35+",
                "n": 12,
                "reliable": False,
                "base_rate": 0.5,
                "selection_rate": 0.2,
                "tpr": 0.5,
                "fpr": 0.0,
                "brier": 0.1,
            },
            {
                "attribute": "age_band",
                "operating_point": "top_k=20",
                "group": "35+",
                "n": 12,
                "reliable": False,
                "base_rate": 0.5,
                "selection_rate": 0.2,
                "tpr": 0.5,
                "fpr": 0.0,
                "brier": 0.1,
            },
        ],
        "attribute_summary": [
            {
                "attribute": "gender",
                "operating_point": "threshold",
                "reference_group": "female",
                "n_groups": 2,
                "n_reliable_groups": 2,
                "dp_difference": 0.04,
                "di_ratio": 0.56,
                "eo_difference": 0.01,
                "eq_odds_max_diff": 0.01,
            },
            {
                "attribute": "age_band",
                "operating_point": "threshold",
                "reference_group": "17-19",
                "n_groups": 4,
                "n_reliable_groups": 3,
                "dp_difference": 0.2,
                "di_ratio": 0.1,
                "eo_difference": 0.4,
                "eq_odds_max_diff": 0.4,
            },
        ],
        "mitigation": [
            {
                "variant": "baseline (deployed)",
                "deployable": True,
                "pr_auc": 0.8,
                "recall_at_k": 0.17,
                "gender_dp_difference": 0.02,
                "gender_eo_difference": 0.02,
                "age_band_eo_difference": 0.14,
            }
        ],
        "figures": {"selection_rates": None, "group_calibration": None},
    }
    test_k = pd.DataFrame(
        [
            {
                "window_weeks": w,
                "capacity_k_illustrative": 10 * w,
                "recall_at_k_measured": 0.05 * w,
                "precision_at_k_measured": 0.9,
                "dropouts_in_test": 100,
            }
            for w in (2, 5, 10)
        ]
    )
    return AppState(
        cfg=cfg,
        bundle=bundle,
        cohort=cohort,
        ranked=ranked,
        shap=shap,
        rules=rules,
        reference={},
        fields=build_fields(bundle.schema, allow, rules),
        equity=equity,
        model_card_md="# Model Card\n\nFixture card.",
        limitations_md="fixture limits",
        test_k=test_k,
        action_log=ActionLog(tmp / "actions.sqlite"),
        k_default=50,
        k_options=k_options(cfg),
        per_week=10,
        window_weeks=5,
        disclaimer=DISCLAIMER,
        non_use="No adverse decisions.",
    )


def render_json(component) -> str:
    """Full recursive JSON of a Dash component tree (the encoder Dash uses to serve layouts)."""
    return json.dumps(component, cls=PlotlyJSONEncoder, ensure_ascii=False)
