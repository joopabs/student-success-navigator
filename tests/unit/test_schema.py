from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from ssn.config import load
from ssn.data import schema as S
from ssn.features import allowlist as al
from ssn.features.allowlist import LeakageError


def _write_csv(tmp_path: Path, df: pd.DataFrame, name: str = "d.csv") -> Path:
    p = tmp_path / name
    df.to_csv(p, sep=";", index=False, encoding="utf-8-sig")
    return p


def test_load_raw_normalises_headers(tmp_path, synthetic_frame):
    df = synthetic_frame.rename(columns={"enrol_evening": "enrol_evening\t"})
    p = _write_csv(tmp_path, df)
    loaded = S.load_raw(p)
    assert "enrol_evening" in loaded.columns
    assert loaded.shape == synthetic_frame.shape


def test_load_raw_missing_file_has_actionable_message(tmp_path):
    with pytest.raises(S.SchemaError, match="data download"):
        S.load_raw(tmp_path / "nope.csv")


def test_valid_fixture_passes(synthetic_frame, features_yaml):
    cfg = load("configs/base.yaml", set_seeds=False)
    report = S.validate(synthetic_frame, cfg, al.load(features_yaml))
    assert report.errors == []
    assert report.n_rows == len(synthetic_frame)
    assert set(report.target_labels_observed) == {"Dropout", "Enrolled", "Graduate"}
    S.raise_for_errors(report)


def test_wrong_target_label_fails(synthetic_frame, features_yaml):
    cfg = load("configs/base.yaml", set_seeds=False)
    df = synthetic_frame.copy()
    df.loc[df.index[0], "Target"] = "Withdrawn"
    report = S.validate(df, cfg, al.load(features_yaml))
    assert any("Target labels differ" in e for e in report.errors)
    with pytest.raises(S.SchemaError):
        S.raise_for_errors(report)


def test_missing_column_fails(synthetic_frame, features_yaml):
    cfg = load("configs/base.yaml", set_seeds=False)
    report = S.validate(synthetic_frame.drop(columns=["sem1_grade"]), cfg, al.load(features_yaml))
    assert any("absent from data" in e for e in report.errors)


def test_extra_unclassified_column_is_a_leakage_error(synthetic_frame, features_yaml):
    cfg = load("configs/base.yaml", set_seeds=False)
    report = S.validate(synthetic_frame.assign(mystery=1), cfg, al.load(features_yaml))
    assert any("unclassified" in e for e in report.errors)
    with pytest.raises(LeakageError):
        S.raise_for_errors(report)


def test_binary_column_with_bad_values_fails(synthetic_frame, features_yaml):
    cfg = load("configs/base.yaml", set_seeds=False)
    df = synthetic_frame.copy()
    df.loc[df.index[0], "enrol_evening"] = 7
    report = S.validate(df, cfg, al.load(features_yaml))
    assert any("binary column has values" in e for e in report.errors)


def test_verified_encoding_with_undocumented_code_fails(tmp_path, synthetic_frame):
    import yaml

    cols = [
        {
            "name": "enrol_course_code",
            "availability": "enrollment",
            "role": "feature",
            "dtype": "categorical",
            "adviser_visible": True,
            "encoding_verified": True,
            "codes": {11: "A", 22: "B"},
        },  # 33 observed but undocumented
        {
            "name": "Target",
            "availability": "outcome",
            "role": "target",
            "dtype": "categorical",
            "adviser_visible": False,
        },
    ]
    p = tmp_path / "f.yaml"
    p.write_text(yaml.safe_dump({"columns": cols, "engineered": []}))
    cfg = load("configs/base.yaml", set_seeds=False)
    df = synthetic_frame[["enrol_course_code", "Target"]]
    report = S.validate(df, cfg, al.load(p))
    assert any("outside documentation" in e for e in report.errors)
    chk = {c.name: c for c in report.column_checks}["enrol_course_code"]
    assert chk.encoding_check == "mismatch" and chk.observed_outside_codes == [33]
