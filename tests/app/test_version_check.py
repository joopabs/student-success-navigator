from __future__ import annotations

import pytest

from ssn.app import state as S
from ssn.app.app import create_app, route
from ssn.config import load


def test_blocked_state_when_artifact_missing(tmp_path, monkeypatch):
    cfg = load("configs/base.yaml", set_seeds=False)
    real = cfg.__class__.path_for

    def redirect(self, key):
        return (
            tmp_path / key
            if key in {"models_dir", "demo_dir", "app.actions_db"}
            else real(self, key)
        )

    monkeypatch.setattr(cfg.__class__, "path_for", redirect)
    called = []
    monkeypatch.setattr(S, "score_frame", lambda *a, **k: called.append(1))
    st = S.load_state(cfg)
    assert st.blocked and "failed verification" in st.blocked_reason
    assert called == []  # scoring never invoked
    app = create_app(cfg, state=st)
    from tests.app.conftest import render_json

    text = render_json(route(st, "/queue"))
    assert "not serving scores" in text and "open-ack" not in text
    assert "SSN_STATE" in app.server.config


@pytest.mark.needs_data
def test_version_mismatch_blocks_with_real_artifact(monkeypatch):
    from pathlib import Path

    if not Path("models/final_pipeline.joblib").is_file():
        pytest.skip("real artifact not present")
    cfg = load("configs/base.yaml", set_seeds=False)
    monkeypatch.setitem(cfg.raw["app"], "expected_model_version", "9.9.9")
    st = S.load_state(cfg)
    assert st.blocked and "model_version" in st.blocked_reason
