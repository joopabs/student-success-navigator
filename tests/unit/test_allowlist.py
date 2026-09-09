from __future__ import annotations

import pytest
import yaml

from ssn.features import allowlist as al


def test_classification_sets(features_yaml):
    a = al.load(features_yaml)
    assert a.allowed_source == {
        "enrol_admission_grade",
        "enrol_course_code",
        "enrol_evening",
        "sem1_enrolled",
        "sem1_approved",
        "sem1_grade",
    }
    assert "sem1_approval_rate" in a.allowed
    assert "age_band" not in a.allowed and "age_band" in a.engineered
    assert a.sensitive == {"sens_gender", "sens_age"}
    assert a.ambiguous == {"fin_status_flag"}
    assert "fin_status_flag" in a.prohibited and "sem2_approved" in a.prohibited
    assert a.target == "Target"
    assert "sens_gender" not in a.adviser_visible


def test_projected_frame_passes(features_yaml, synthetic_frame):
    a = al.load(features_yaml)
    X = a.project_features(synthetic_frame)
    assert set(X.columns) == a.allowed_source  # engineered not yet computed on raw frame
    a.assert_frame_allowed(X)  # no raise


def test_full_frame_with_label_raises(features_yaml, synthetic_frame):
    a = al.load(features_yaml)
    with pytest.raises(al.LeakageError, match="Target"):
        a.assert_frame_allowed(synthetic_frame)


def test_prohibited_second_semester_column_raises(features_yaml, synthetic_frame):
    a = al.load(features_yaml)
    X = a.project_features(synthetic_frame).assign(sem2_approved=synthetic_frame["sem2_approved"])
    with pytest.raises(al.LeakageError, match="sem2_approved.*prohibited"):
        a.assert_frame_allowed(X)


def test_unclassified_column_raises(features_yaml, synthetic_frame):
    a = al.load(features_yaml)
    X = a.project_features(synthetic_frame).assign(mystery_col=1)
    with pytest.raises(al.LeakageError, match="mystery_col.*unclassified"):
        a.assert_frame_allowed(X)
    with pytest.raises(al.LeakageError, match="Unclassified columns"):
        a.assert_all_classified([*synthetic_frame.columns, "mystery_col"])


def test_sensitive_column_raises(features_yaml, synthetic_frame):
    a = al.load(features_yaml)
    X = a.project_features(synthetic_frame).assign(sens_gender=synthetic_frame["sens_gender"])
    with pytest.raises(al.LeakageError, match="sens_gender.*sensitive"):
        a.assert_frame_allowed(X)


def test_all_classified_passes_for_fixture(features_yaml, synthetic_frame):
    al.load(features_yaml).assert_all_classified(synthetic_frame.columns)


def test_empty_skeleton_allows_nothing():
    a = al.build({"columns": [], "engineered": []})
    assert a.allowed == frozenset() and a.columns == {} and a.target is None


def test_engineered_with_prohibited_input_is_rejected(tmp_path):
    raw = {
        "columns": [
            {
                "name": "sem2_x",
                "availability": "second_semester",
                "role": "feature",
                "dtype": "numeric",
                "adviser_visible": False,
            }
        ],
        "engineered": [{"name": "leaky", "inputs": ["sem2_x"], "adviser_visible": True}],
    }
    p = tmp_path / "f.yaml"
    p.write_text(yaml.safe_dump(raw))
    with pytest.raises(al.AllowlistConfigError, match="non-allow-listed inputs"):
        al.load(p)


def test_sensitive_cannot_be_adviser_visible(tmp_path):
    raw = {
        "columns": [
            {
                "name": "g",
                "availability": "enrollment",
                "role": "sensitive",
                "dtype": "categorical",
                "adviser_visible": True,
            }
        ]
    }
    p = tmp_path / "f.yaml"
    p.write_text(yaml.safe_dump(raw))
    with pytest.raises(al.AllowlistConfigError, match="adviser_visible"):
        al.load(p)
