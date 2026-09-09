from __future__ import annotations

import pandas as pd

from ssn.config import load
from ssn.data import clean as C
from ssn.features import allowlist as al


def _run(df, features_yaml):
    cfg = load("configs/base.yaml", set_seeds=False)
    return C.clean(df, cfg, al.load(features_yaml))


def test_clean_fixture_is_noop_and_logs_every_issue(synthetic_frame, features_yaml):
    res = _run(synthetic_frame, features_yaml)
    tbl = res.table()
    assert len(res.frame) == len(synthetic_frame)
    assert set(tbl.columns) == {"issue", "column", "count_before", "count_after", "treatment"}
    for issue in (
        "exact duplicate rows",
        "undocumented Target label",
        "rows with any missing value",
        "rows",
    ):
        assert issue in set(tbl["issue"]), issue
    assert (tbl["treatment"].str.len() > 0).all()


def test_duplicates_are_dropped_and_counted(synthetic_frame, features_yaml):
    df = pd.concat([synthetic_frame, synthetic_frame.iloc[:3]], ignore_index=True)
    res = _run(df, features_yaml)
    row = res.table().set_index("issue").loc["exact duplicate rows"]
    assert row["count_before"] == 3 and row["count_after"] == 0
    assert len(res.frame) == len(synthetic_frame)


def test_bad_target_label_row_is_dropped(synthetic_frame, features_yaml):
    df = synthetic_frame.copy()
    df.loc[df.index[:2], "Target"] = "Unknown"
    res = _run(df, features_yaml)
    assert len(res.frame) == len(synthetic_frame) - 2
    assert set(res.frame["Target"]) <= {"Dropout", "Enrolled", "Graduate"}


def test_missing_value_row_is_dropped(synthetic_frame, features_yaml):
    df = synthetic_frame.copy()
    df.loc[df.index[0], "sem1_grade"] = None
    res = _run(df, features_yaml)
    assert len(res.frame) == len(synthetic_frame) - 1
    assert res.table().set_index("issue").loc["rows with any missing value", "count_before"] == 1


def test_outliers_and_zero_enrollment_are_kept(synthetic_frame, features_yaml):
    df = synthetic_frame.copy()
    df["Curricular units 1st sem (enrolled)"] = df["sem1_enrolled"]
    df["Curricular units 1st sem (approved)"] = df["sem1_approved"]
    df["Curricular units 1st sem (grade)"] = df["sem1_grade"]
    # extra columns are not in the fixture allow-list; clean() only iterates allow columns
    res = _run(df, features_yaml)
    n_zero = int((df["sem1_enrolled"] == 0).sum())
    tbl = res.table().set_index("issue")
    assert tbl.loc["zero units enrolled (1st sem)", "count_before"] == n_zero
    assert tbl.loc["zero units enrolled (1st sem)", "count_after"] == n_zero  # kept
    assert len(res.frame) == len(df)
