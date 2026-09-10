from __future__ import annotations

import pandas as pd
import pytest

from ssn.reporting import model_card as MC


def _manifest(evaluated: bool):
    return {
        "model_version": "1.0.0",
        "created_at": "2026-09-10T00:00:00Z",
        "git_sha": "abc123",
        "seed": 42,
        "disclaimer": "Scores are illustrative decision support. Not production-ready.",
        "intended_use": "Decision support.",
        "non_use": "No adverse decisions.",
        "data": {
            "source": "UCI 697",
            "doi": "x",
            "license": "CC BY 4.0",
            "n_train": 10,
            "n_test": 5,
            "positive_rate_train": 0.3,
            "positive_rate_test": 0.3,
            "raw_sha256": "0" * 64,
        },
        "target": {
            "name": "is_dropout",
            "positive_label": "Dropout",
            "negative_labels": ["Enrolled", "Graduate"],
        },
        "features": {
            "allowlisted_source": ["a"],
            "engineered": ["e"],
            "prohibited_excluded": ["s2"],
            "ambiguous_excluded": ["Debtor"],
            "sensitive_excluded_audit_only": ["Gender"],
            "selection_setting": None,
        },
        "estimator": {"class": "sklearn.ensemble.RandomForestClassifier"},
        "imbalance_treatment": "class_weight",
        "calibration": {"applied": True, "method": "isotonic"},
        "selection_rationale": "rule",
        "python_version": "3.11",
        "library_versions": {"scikit-learn": "1.9"},
        "threshold": {
            "rule": "cap",
            "capacity_per_week": 10,
            "window_weeks": 5,
            "capacity_k": 50,
            "n_cohort_expected": 885,
            "value": 0.9,
            "selection_rate_oof": 0.057,
        },
        "bands": [{"name": "Priority outreach", "lower": 0.9, "upper": 1.0, "rule": "top"}],
        "cv_summary": {
            "pr_auc": 0.8,
            "pr_auc_std_cv": 0.01,
            "recall_at_k": 0.17,
            "brier": 0.13,
            "ece": 0.05,
        },
        "test_evaluations": 1 if evaluated else 0,
        "test_summary": {"pr_auc": 0.8 if evaluated else None},
        "zero_predicted_positives_on_test": False,
        "config_sha256": "1" * 64,
        "pipeline_sha256": "2" * 64,
        "measured_vs_illustrative": "measured vs illustrative note",
    }


TEST_METRICS = pd.DataFrame(
    [
        {
            "pr_auc": 0.8,
            "roc_auc": 0.88,
            "recall_at_k": 0.17,
            "precision_at_k": 0.96,
            "brier": 0.12,
            "ece": 0.03,
            "precision_at_threshold": 0.96,
            "recall_at_threshold": 0.19,
            "k": 50,
        }
    ]
)
TEST_K = pd.DataFrame(
    [
        {
            "window_weeks": 5,
            "capacity_k_illustrative": 50,
            "recall_at_k_measured": 0.17,
            "precision_at_k_measured": 0.96,
            "dropouts_in_test": 284,
        }
    ]
)


def test_render_fails_on_placeholders(tmp_path):
    with pytest.raises(MC.ModelCardError, match="placeholders"):
        MC.render(
            _manifest(False), TEST_METRICS, TEST_K, None, "limits", None, tmp_path / "card.md"
        )


def test_render_fails_on_overclaim(tmp_path):
    with pytest.raises(MC.ModelCardError, match="over-claim"):
        MC.render(
            _manifest(True),
            TEST_METRICS,
            TEST_K,
            None,
            "Therefore the model is fair.",
            None,
            tmp_path / "card.md",
        )


def test_render_contains_required_sections(tmp_path):
    text = MC.render(
        _manifest(True),
        TEST_METRICS,
        TEST_K,
        None,
        "Limitations text here.",
        {
            "method": "shap.TreeExplainer",
            "ensemble_members": 5,
            "aggregation": "agg",
            "explains": "uncalibrated",
        },
        tmp_path / "card.md",
    )
    for heading in (
        "## Intended use",
        "## Out-of-scope use",
        "## Data",
        "## Model",
        "## Operating point",
        "## Performance",
        "## Explainability",
        "## Fairness",
        "## Limitations",
        "## Provenance",
    ):
        assert heading in text, heading
    assert (
        "ILLUSTRATIVE" in text
        and "Not production-ready" in text
        and "Fairness audit not yet run" in text
    )
    assert (tmp_path / "card.md").exists()
