from __future__ import annotations

import numpy as np
import pytest
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.pipeline import Pipeline

from ssn.config import load
from ssn.features import allowlist as al
from ssn.features.preprocess import feature_groups, project_for_model
from ssn.modeling import candidates as C


@pytest.fixture(scope="module")
def cfg():
    return load("configs/base.yaml", set_seeds=False)


@pytest.fixture(scope="module")
def allow():
    return al.load("configs/features.yaml")


SEL = C.SelectionSetting(kind="embedded", method="l1_logreg", k=12)


@pytest.mark.parametrize("name", C.CANDIDATES)
def test_each_candidate_builds_with_seed_and_class_weight(name, cfg, allow):
    pipe = C.build_pipeline(name, cfg, allow, selection=SEL)
    clf = pipe.named_steps["clf"]
    assert clf.get_params().get("random_state") == cfg.seed
    if name in {"logreg", "hist_gb"}:
        assert clf.get_params()["class_weight"] == "balanced"
    if name == "random_forest":
        assert clf.get_params()["class_weight"] == "balanced_subsample"
    steps = [s for s, _ in pipe.steps]
    assert steps[0] == "pre" and steps[-1] == "clf"
    assert ("select" in steps) == (name != "dummy")  # dummy has use_selection: false


def test_smote_variant_uses_imblearn_pipeline_and_correct_mask(cfg, allow, real_named_frame):
    pipe = C.build_pipeline("logreg", cfg, allow, smote=True)
    assert isinstance(pipe, ImbPipeline) and "smote" in dict(pipe.steps)
    smote = pipe.named_steps["smote"]
    assert smote.n_numeric == len(feature_groups(allow)["numeric"])
    X = project_for_model(real_named_frame, allow)
    y = real_named_frame["is_dropout"]
    pipe.fit(X, y)  # fits on fixture rows only
    # after preprocessing, columns >= n_numeric are binary/one-hot -> resampled rows stay 0/1
    Xt = pipe.named_steps["pre"].transform(X)
    Xr, yr = smote.fit_resample(Xt, y)
    assert len(yr) > len(y) and yr.mean() == pytest.approx(0.5, abs=0.02)
    cat_block = Xr[:, smote.n_numeric :]
    assert set(np.unique(cat_block)) <= {0.0, 1.0}


def test_no_smote_variant_is_plain_sklearn_pipeline(cfg, allow):
    pipe = C.build_pipeline("random_forest", cfg, allow)
    assert isinstance(pipe, Pipeline) and not isinstance(pipe, ImbPipeline)
    assert "select" not in dict(pipe.steps)  # no selection setting given


def test_pca_override_adds_step(cfg, allow):
    pipe = C.build_pipeline("logreg", cfg, allow, use_pca=True)
    assert "pca" in dict(pipe.steps)


def test_describe_reports_estimator_and_steps(cfg, allow):
    from ssn.config import load_model_config

    pipe = C.build_pipeline("hist_gb", cfg, allow, selection=SEL)
    d = C.describe(pipe, "hist_gb", load_model_config("hist_gb", cfg))
    assert d["estimator"].endswith("HistGradientBoostingClassifier")
    assert d["steps"] == "pre>select>clf" and "class_weight=balanced" in d["key_params"]
