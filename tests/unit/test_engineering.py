from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ssn.features import allowlist as al
from ssn.features import engineering as E
from ssn.features import preprocess as PP


def test_every_engineered_input_is_allow_listed():
    allow = al.load("configs/features.yaml")
    t = E.Sem1FeatureEngineer()
    bad = [c for c in t.get_input_columns() if c not in allow.allowed_source]
    assert not bad, bad
    for name, (inputs, rationale) in E.FEATURE_SPECS.items():
        assert rationale and len(rationale) > 20, name
        assert all(c in allow.allowed_source for c in inputs), name
        assert name in allow.allowed_engineered, name


def test_no_second_semester_sensitive_or_outcome_inputs():
    t = E.Sem1FeatureEngineer()
    for c in t.get_input_columns():
        assert "2nd sem" not in c
        assert c not in {
            "Gender",
            "Age at enrollment",
            "Nacionality",
            "International",
            "Marital status",
            "Educational special needs",
            "Target",
        }


def test_zero_denominator_yields_nan_and_is_counted(real_named_frame):
    df = real_named_frame.drop(columns=["is_dropout"])
    eng = E.engineer(df)
    zero = df[E.SEM1["enrolled"]] == 0
    assert eng.loc[zero, "sem1_approval_rate"].isna().all()
    assert eng.loc[~zero, "sem1_approval_rate"].between(0, 1).all()
    counts = E.zero_denominator_counts(df)
    assert (counts["n_zero_denominator"] == int(zero.sum())).all()


def test_grade_diff_uses_documented_scales(real_named_frame):
    df = real_named_frame.drop(columns=["is_dropout"])
    eng = E.engineer(df)
    expected = df[E.SEM1["grade"]] * 10.0 - df[E.ADMISSION_GRADE]
    pd.testing.assert_series_equal(
        eng["grade_diff_vs_admission"], expected.rename("grade_diff_vs_admission")
    )


def test_transformer_is_stateless_and_names_out(real_named_frame):
    df = real_named_frame.drop(columns=["is_dropout"])
    t = E.Sem1FeatureEngineer().fit(df)
    out = t.transform(df)
    assert list(out.columns) == list(df.columns) + E.ENGINEERED_NAMES
    assert list(t.get_feature_names_out()) == list(df.columns) + E.ENGINEERED_NAMES
    # fitting on a different frame changes nothing about transform outputs
    t2 = E.Sem1FeatureEngineer().fit(df.iloc[:5])
    pd.testing.assert_frame_equal(t2.transform(df), out)


def test_age_band_mapping_and_empty_bands():
    age = pd.Series([17, 19, 20, 24, 25, 34, 35, 70])
    bands = [
        {"name": "17-19", "lower": 17, "upper": 19},
        {"name": "20-24", "lower": 20, "upper": 24},
        {"name": "25-34", "lower": 25, "upper": 34},
        {"name": "35+", "lower": 35, "upper": 120},
    ]
    assert list(E.age_band(age, bands)) == [
        "17-19",
        "17-19",
        "20-24",
        "20-24",
        "25-34",
        "25-34",
        "35+",
        "35+",
    ]
    assert E.age_band(age, []).isna().all()


def test_preprocessor_builds_and_fits_on_fixture_only(real_named_frame):
    allow = al.load("configs/features.yaml")
    df = real_named_frame.drop(columns=["is_dropout"])
    X = PP.project_for_model(df, allow)
    pre = PP.build_preprocessor(allow)
    Xt = pre.fit_transform(X)
    names = pre.named_steps["columns"].get_feature_names_out()
    assert Xt.shape == (len(df), len(names))
    assert not np.isnan(Xt).any()  # imputation inside the pipeline handled the NaN rates
    assert any("sem1_approval_rate" in n for n in names)
    groups = PP.feature_groups(allow)
    assert set(groups["numeric"]) >= set(E.ENGINEERED_NAMES)
    assert not ({*groups["numeric"], *groups["binary"], *groups["categorical"]} & allow.sensitive)


def test_project_for_model_rejects_sensitive_and_second_semester(real_named_frame):
    allow = al.load("configs/features.yaml")
    df = real_named_frame.drop(columns=["is_dropout"]).copy()
    df["Gender"] = 1
    df["Curricular units 2nd sem (grade)"] = 10.0
    X = PP.project_for_model(df, allow)
    assert "Gender" not in X.columns and "Curricular units 2nd sem (grade)" not in X.columns
    with pytest.raises(al.LeakageError):
        allow.assert_frame_allowed(df)
