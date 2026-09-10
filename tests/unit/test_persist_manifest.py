from __future__ import annotations

import pytest

from ssn.config import load
from ssn.features import allowlist as al
from ssn.features.preprocess import project_for_model
from ssn.modeling import persist as PS

CONTRACT_KEYS = {
    "model_version",
    "created_at",
    "git_sha",
    "config_sha256",
    "pipeline_file",
    "pipeline_sha256",
    "python_version",
    "library_versions",
    "seed",
    "data",
    "target",
    "features",
    "estimator",
    "calibration",
    "imbalance_treatment",
    "threshold",
    "bands",
    "selection_rationale",
    "cv_summary",
    "test_evaluations",
    "test_summary",
    "fairness_summary_file",
    "explainability_files",
    "intended_use",
    "non_use",
    "disclaimer",
}


@pytest.fixture()
def fixture_artifact(tmp_path, real_named_frame):
    cfg = load("configs/base.yaml", set_seeds=False)
    allow = al.load("configs/features.yaml")
    train = real_named_frame.copy()
    decision = {
        "model": "logreg",
        "selection": "none",
        "best_params": {"C": 0.5},
        "rationale": "fixture",
        "rule": "fixture",
    }
    calibration = {"applied": False, "method": None}
    threshold = {
        "rule": "oof_quantile_for_capacity",
        "capacity_per_week": 10,
        "window_weeks": 5,
        "capacity_k": 50,
        "n_cohort_expected": 885,
        "threshold": 0.6,
        "selection_rate": 0.057,
        "bands": [
            {"name": "Priority outreach", "lower": 0.6, "upper": 1.0},
            {"name": "Check-in suggested", "lower": 0.4, "upper": 0.6},
            {"name": "Standard support", "lower": 0.0, "upper": 0.4},
        ],
    }
    matrix_row = {
        k: 0.5
        for k in [
            "pr_auc",
            "pr_auc_std_cv",
            "roc_auc",
            "recall_at_k",
            "precision_at_k",
            "brier",
            "ece",
            "fairness_max_dp_difference",
            "fairness_min_di_ratio",
        ]
    }
    models_dir = tmp_path / "models"
    manifest = PS.fit_and_persist(
        train,
        cfg,
        allow,
        decision,
        calibration,
        threshold,
        matrix_row,
        None,
        models_dir,
        "deadbeef",
        {"Admission grade": {"min": 95.0, "max": 190.0}},
    )
    return cfg, allow, models_dir, manifest, train


def test_manifest_has_every_contract_key_and_no_row_level_data(fixture_artifact):
    _, _, models_dir, manifest, _ = fixture_artifact
    assert CONTRACT_KEYS <= set(manifest)
    text = (models_dir / PS.MANIFEST_FILE).read_text()
    assert "record_id" not in text and "R00000001" not in text
    assert manifest["test_evaluations"] == 0 and all(
        v is None for v in manifest["test_summary"].values()
    )
    assert manifest["threshold"]["capacity_illustrative"] is True
    assert "ILLUSTRATIVE" in manifest["measured_vs_illustrative"]
    assert "not production-ready" in manifest["disclaimer"]


def test_pipeline_sha_matches_file_and_load_verifies(fixture_artifact):
    cfg, _, models_dir, manifest, _ = fixture_artifact
    assert manifest["pipeline_sha256"] == PS.sha256_file(models_dir / PS.PIPELINE_FILE)
    loaded_manifest, pipe = PS.load_artifact(
        models_dir, expected_version=cfg.get("project.model_version")
    )
    assert loaded_manifest["pipeline_sha256"] == manifest["pipeline_sha256"]
    assert hasattr(pipe, "predict_proba")


def test_load_artifact_rejects_tampered_file_and_wrong_version(fixture_artifact):
    _, _, models_dir, _, _ = fixture_artifact
    with pytest.raises(PS.ArtifactError, match="model_version"):
        PS.load_artifact(models_dir, expected_version="9.9.9")
    (models_dir / PS.PIPELINE_FILE).write_bytes(b"corrupted")
    with pytest.raises(PS.ArtifactError, match="sha256 mismatch"):
        PS.load_artifact(models_dir)


def test_loaded_pipeline_predicts_on_schema_conforming_frame(fixture_artifact):
    _, allow, models_dir, manifest, train = fixture_artifact
    _, pipe = PS.load_artifact(models_dir)
    X = project_for_model(train, allow)
    assert PS.validate_input_frame(X, manifest) == []
    p = pipe.predict_proba(X)[:, 1]
    assert p.shape == (len(X),) and ((p >= 0) & (p <= 1)).all()


def test_input_schema_lists_exact_allowed_columns_with_codes_or_ranges(fixture_artifact):
    _, allow, _, manifest, train = fixture_artifact
    schema = manifest["features"]["input_schema"]
    assert [c["name"] for c in schema] == sorted(allow.allowed_source)
    coded = {c["name"] for c in schema if "allowed_codes" in c}
    assert "Course" in coded and "Gender" not in {c["name"] for c in schema}
    assert next(c for c in schema if c["name"] == "Admission grade")["observed_range_raw"] == {
        "min": 95.0,
        "max": 190.0,
    }
    X = (
        project_for_model(train, allow)
        .drop(columns=["Course"])
        .assign(**{"Curricular units 2nd sem (grade)": 1.0})
    )
    problems = PS.validate_input_frame(X, manifest)
    assert any("missing" in p for p in problems) and any("unexpected" in p for p in problems)


def test_manifest_features_exclude_sensitive_and_second_semester(fixture_artifact):
    _, allow, _, manifest, _ = fixture_artifact
    f = manifest["features"]
    assert set(f["sensitive_excluded_audit_only"]) == set(allow.sensitive)
    assert all(c.startswith("Curricular units 2nd sem") for c in f["prohibited_excluded"])
    assert not (set(f["allowlisted_source"]) & set(allow.sensitive))
    assert set(f["ambiguous_excluded"]) == {
        "Debtor",
        "Tuition fees up to date",
        "Scholarship holder",
    }
