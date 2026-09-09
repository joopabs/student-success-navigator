"""Structural checks on the real configs/features.yaml (no data needed) plus a needs_data check
that every observed raw column is classified exactly once."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ssn.features import allowlist as al

SENSITIVE_POLICY = {  # PROJECT_DECISIONS.md: audit-only, never model inputs
    "Gender",
    "Age at enrollment",
    "Nacionality",
    "International",
    "Marital status",
    "Educational special needs",
}
AMBIGUOUS_POLICY = {"Debtor", "Tuition fees up to date", "Scholarship holder"}  # research R-05


@pytest.fixture(scope="module")
def allow() -> al.Allowlist:
    return al.load("configs/features.yaml")


def test_thirty_seven_columns_classified(allow):
    assert len(allow.columns) == 37
    assert allow.target == "Target"


def test_sensitive_policy_applied(allow):
    assert allow.sensitive == SENSITIVE_POLICY
    assert not (allow.sensitive & allow.allowed)
    for name in SENSITIVE_POLICY:
        assert allow.columns[name]["adviser_visible"] is False


def test_second_semester_outcome_and_ambiguous_are_prohibited(allow):
    second = {n for n, m in allow.columns.items() if m["availability"] == "second_semester"}
    assert len(second) == 6 and all(n.startswith("Curricular units 2nd sem") for n in second)
    assert second <= allow.prohibited
    assert allow.ambiguous == AMBIGUOUS_POLICY and allow.ambiguous <= allow.prohibited
    assert "Target" not in allow.allowed


def test_first_semester_columns_are_allowed(allow):
    first = {n for n, m in allow.columns.items() if m["availability"] == "first_semester"}
    assert len(first) == 6 and first <= allow.allowed


def test_allowed_count_matches_policy(allow):
    # 37 total - 6 second-semester - 3 ambiguous - 6 sensitive - 1 target = 21
    assert len(allow.allowed_source) == 21


def test_every_coded_column_has_source_and_verification_flag(allow):
    for name, meta in allow.columns.items():
        if meta["dtype"] in {"categorical", "binary"} and name != "Target":
            assert meta.get("codes"), f"{name}: coded column without documented codes"
            assert "encoding_verified" in meta, name
            assert "UCI" in meta.get("encoding_source", ""), name


def test_gender_encoding_documented_and_verified(allow):
    g = allow.columns["Gender"]
    assert g["codes"] == {1: "male", 0: "female"}
    assert g["encoding_verified"] is True
    assert g["role"] == "sensitive"


def test_each_column_appears_once_in_yaml():
    raw = yaml.safe_load(Path("configs/features.yaml").read_text())
    names = [c["name"] for c in raw["columns"]]
    assert len(names) == len(set(names))


@pytest.mark.needs_data
def test_observed_columns_all_classified(allow):
    from ssn.data.schema import load_raw

    p = Path("data/raw/data.csv")
    if not p.is_file():
        pytest.skip("raw data not present; run `python -m ssn data download`")
    df = load_raw(p)
    allow.assert_all_classified(df.columns)
    assert df.shape == (4424, 37)
