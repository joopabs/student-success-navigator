"""Group labels for fairness auditing (T049).

Gender uses the encoding documented in configs/features.yaml and REFUSES to run unless that
encoding is marked verified (constitution Principle X, spec FR-045). Age bands come from
configs/base.yaml (PV-06). Sensitive attributes are used here for aggregate auditing only.
"""

from __future__ import annotations

import pandas as pd

from ssn.config import Config
from ssn.features.allowlist import Allowlist
from ssn.features.engineering import age_band

GENDER_COL = "Gender"
AGE_COL = "Age at enrollment"
AGE_BAND = "age_band"


class UnverifiedEncodingError(RuntimeError):
    """A sensitive attribute's encoding is not verified against source documentation."""


def gender_labels(frame: pd.DataFrame, allow: Allowlist) -> pd.Series:
    meta = allow.columns.get(GENDER_COL)
    if meta is None or not meta.get("codes"):
        raise UnverifiedEncodingError(f"{GENDER_COL!r} has no documented codes in features.yaml")
    if not meta.get("encoding_verified"):
        raise UnverifiedEncodingError(
            f"{GENDER_COL!r} encoding is not marked encoding_verified in features.yaml; "
            "the fairness audit refuses to guess a mapping (PV-04)"
        )
    codes = {int(k): str(v) for k, v in meta["codes"].items()}
    return frame[GENDER_COL].astype(int).map(codes).rename("gender")


def age_band_labels(frame: pd.DataFrame, cfg: Config) -> pd.Series:
    if AGE_BAND in frame.columns and frame[AGE_BAND].notna().all():
        return frame[AGE_BAND].astype(str).rename("age_band")
    bands = cfg.get("fairness.age_bands")
    if not bands:
        raise UnverifiedEncodingError(
            "fairness.age_bands is empty; run PV-06 before auditing by age"
        )
    return age_band(frame[AGE_COL], bands).astype(str).rename("age_band")


def group_frame(frame: pd.DataFrame, cfg: Config, allow: Allowlist) -> pd.DataFrame:
    """One column per configured fairness attribute, aligned to frame.index."""
    out = pd.DataFrame(index=frame.index)
    for attr in cfg.get("fairness.attributes"):
        if attr == "gender":
            out["gender"] = gender_labels(frame, allow)
        elif attr == "age_band":
            out["age_band"] = age_band_labels(frame, cfg)
        else:
            raise ValueError(
                f"fairness attribute {attr!r} requires documented ethical justification "
                "(PROJECT_DECISIONS) and an explicit mapping; none is defined"
            )
    return out
