from __future__ import annotations

import json

from ssn.config import load
from ssn.data import profile as P
from ssn.data import schema as S
from ssn.features import allowlist as al
from ssn.reporting import tables as T


def test_profile_outputs_on_fixture(tmp_path, synthetic_frame, features_yaml):
    cfg = load("configs/base.yaml", set_seeds=False)
    allow = al.load(features_yaml)
    out = P.run_profile(synthetic_frame, cfg, allow)

    assert set(out.columns["column"]) == set(synthetic_frame.columns)
    assert out.target["count"].sum() == len(synthetic_frame)
    assert set(out.target["label"]) == {"Dropout", "Enrolled", "Graduate"}
    assert out.target.attrs["is_dropout_positive_rate"] == round(
        (synthetic_frame["Target"] == "Dropout").mean(), 4
    )
    assert list(out.duplicates["rule"])[0].startswith("exact duplicate")
    assert {"column", "code", "label", "count", "documented"} <= set(out.categorical_values.columns)
    assert (out.invalid_values["count"] >= 0).all()
    assert set(out.ranges) == {c for c, m in allow.columns.items() if m["dtype"] == "numeric"}

    written = P.write_outputs(out, tmp_path / "tables", tmp_path / "ranges.json")
    assert len(written) == 7 and all(p.exists() for p in written)
    assert json.loads((tmp_path / "ranges.json").read_text())["sem1_grade"]["min"] <= 20

    report = S.validate(synthetic_frame, cfg, allow)
    d = T.render_data_dictionary(cfg, allow, out, report, tmp_path / "dict.md")
    o = T.render_data_overview(cfg, allow, out, report, tmp_path / "overview.md", "deadbeef")
    assert "# Data Dictionary" in d and "sem1_approval_rate" in d
    assert "# Data Overview" in o and "deadbeef" in o and str(len(synthetic_frame)) in o


def test_notes_block_survives_regeneration(tmp_path, synthetic_frame, features_yaml):
    cfg = load("configs/base.yaml", set_seeds=False)
    allow = al.load(features_yaml)
    out = P.run_profile(synthetic_frame, cfg, allow)
    report = S.validate(synthetic_frame, cfg, allow)
    path = tmp_path / "overview.md"
    T.render_data_overview(cfg, allow, out, report, path, "x")
    text = path.read_text().replace(
        "_Add hand-written notes here; this block survives regeneration._", "KEEP ME"
    )
    path.write_text(text)
    T.render_data_overview(cfg, allow, out, report, path, "x")
    assert "KEEP ME" in path.read_text()
