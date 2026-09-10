from __future__ import annotations

import pandas as pd
import pytest
import yaml

from ssn.config import load
from ssn.fairness import groups as G
from ssn.features import allowlist as al


def test_gender_labels_use_verified_encoding():
    allow = al.load("configs/features.yaml")
    frame = pd.DataFrame({"Gender": [1, 0, 1]})
    assert list(G.gender_labels(frame, allow)) == ["male", "female", "male"]


def test_gender_refuses_unverified_encoding(tmp_path):
    cols = [
        {
            "name": "Gender",
            "availability": "enrollment",
            "role": "sensitive",
            "dtype": "binary",
            "adviser_visible": False,
            "codes": {1: "male", 0: "female"},
            "encoding_verified": False,
        }
    ]
    p = tmp_path / "f.yaml"
    p.write_text(yaml.safe_dump({"columns": cols, "engineered": []}))
    with pytest.raises(G.UnverifiedEncodingError, match="encoding_verified"):
        G.gender_labels(pd.DataFrame({"Gender": [1, 0]}), al.load(p))


def test_age_band_labels_from_config_and_precomputed_column():
    cfg = load("configs/base.yaml", set_seeds=False)
    frame = pd.DataFrame({"Age at enrollment": [17, 20, 30, 50]})
    assert list(G.age_band_labels(frame, cfg)) == ["17-19", "20-24", "25-34", "35+"]
    pre = frame.assign(age_band=["17-19", "20-24", "25-34", "35+"])
    assert list(G.age_band_labels(pre, cfg)) == ["17-19", "20-24", "25-34", "35+"]


def test_group_frame_has_configured_attributes_only():
    cfg = load("configs/base.yaml", set_seeds=False)
    allow = al.load("configs/features.yaml")
    frame = pd.DataFrame({"Gender": [1, 0], "Age at enrollment": [18, 40]})
    gf = G.group_frame(frame, cfg, allow)
    assert list(gf.columns) == ["gender", "age_band"]


def test_unknown_attribute_requires_justification(monkeypatch):
    cfg = load("configs/base.yaml", set_seeds=False)
    monkeypatch.setitem(cfg.raw["fairness"], "attributes", ["nationality"])
    with pytest.raises(ValueError, match="ethical justification"):
        G.group_frame(pd.DataFrame({"Gender": [1]}), cfg, al.load("configs/features.yaml"))
