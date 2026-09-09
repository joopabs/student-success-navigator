"""Shared pytest fixtures.

The synthetic frame below uses INVENTED column names that mirror the availability classes in
configs/features.yaml. It contains no real student records and no real UCI column names.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

FIXTURE_COLUMNS = [
    # name, availability, role, dtype, adviser_visible
    ("enrol_admission_grade", "enrollment", "feature", "numeric", True),
    ("enrol_course_code", "enrollment", "feature", "categorical", True),
    ("enrol_evening", "enrollment", "feature", "binary", True),
    ("sem1_enrolled", "first_semester", "feature", "numeric", True),
    ("sem1_approved", "first_semester", "feature", "numeric", True),
    ("sem1_grade", "first_semester", "feature", "numeric", True),
    ("fin_status_flag", "ambiguous", "feature", "binary", True),
    ("sem2_approved", "second_semester", "feature", "numeric", False),
    ("sens_gender", "enrollment", "sensitive", "categorical", False),
    ("sens_age", "enrollment", "sensitive", "numeric", False),
    ("Target", "outcome", "target", "categorical", False),
]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def synthetic_frame() -> pd.DataFrame:
    rng = np.random.default_rng(1234)
    n = 60
    sem1_enrolled = rng.integers(0, 8, size=n)
    sem1_approved = np.minimum(sem1_enrolled, rng.integers(0, 8, size=n))
    frame = pd.DataFrame(
        {
            "enrol_admission_grade": rng.normal(130, 12, size=n).round(1),
            "enrol_course_code": rng.choice([11, 22, 33], size=n),
            "enrol_evening": rng.integers(0, 2, size=n),
            "sem1_enrolled": sem1_enrolled,
            "sem1_approved": sem1_approved,
            "sem1_grade": rng.normal(12, 3, size=n).round(2),
            "fin_status_flag": rng.integers(0, 2, size=n),
            "sem2_approved": rng.integers(0, 8, size=n),
            "sens_gender": rng.choice([0, 1], size=n),
            "sens_age": rng.integers(17, 50, size=n),
        }
    )
    frame["Target"] = rng.choice(["Dropout", "Enrolled", "Graduate"], size=n, p=[0.35, 0.2, 0.45])
    return frame


@pytest.fixture()
def features_yaml(tmp_path: Path) -> Path:
    raw = {
        "columns": [
            {
                "name": name,
                "availability": av,
                "role": role,
                "dtype": dtype,
                "adviser_visible": vis,
                "encoding_source": "fixture",
                "encoding_verified": True,
                "note": "synthetic fixture",
            }
            for name, av, role, dtype, vis in FIXTURE_COLUMNS
        ],
        "engineered": [
            {
                "name": "sem1_approval_rate",
                "inputs": ["sem1_approved", "sem1_enrolled"],
                "adviser_visible": True,
            },
            {
                "name": "age_band",
                "inputs": ["sens_age"],
                "adviser_visible": False,
                "audit_only": True,
            },
        ],
    }
    p = tmp_path / "features.yaml"
    p.write_text(yaml.safe_dump(raw))
    return p


@pytest.fixture()
def base_config_dict(repo_root: Path) -> dict:
    return yaml.safe_load((repo_root / "configs" / "base.yaml").read_text())


@pytest.fixture(scope="session")
def real_named_frame() -> pd.DataFrame:
    """Synthetic rows (values invented, seeded) using the REAL allow-listed column names, plus a
    synthetic is_dropout label that depends on the first-semester approval rate so selectors have
    signal to find. No real student rows."""
    from ssn.features import allowlist as al
    from ssn.features import engineering as E

    rng = np.random.default_rng(7)
    n = 240
    allow = al.load(REPO_ROOT / "configs" / "features.yaml")
    df = pd.DataFrame(index=range(n))
    for col in sorted(allow.allowed_source):
        meta = allow.columns[col]
        if meta.get("codes"):
            df[col] = rng.choice([int(k) for k in meta["codes"]], size=n)
        elif meta.get("range"):
            lo, hi = meta["range"]
            df[col] = rng.uniform(lo, hi, size=n).round(1)
        else:
            df[col] = rng.integers(0, 8, size=n)
    enrolled = df[E.SEM1["enrolled"]]
    df[E.SEM1["approved"]] = np.minimum(df[E.SEM1["approved"]], enrolled)
    df.loc[df.index[:5], E.SEM1["enrolled"]] = 0
    rate = (df[E.SEM1["approved"]] / enrolled.replace(0, np.nan)).fillna(0)
    df["is_dropout"] = (rng.random(n) < (0.65 - 0.5 * rate)).astype(int)
    return df
