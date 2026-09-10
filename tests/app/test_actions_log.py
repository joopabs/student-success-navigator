from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

import pytest

from ssn.app.services.action_log import ActionLog

SRC = Path("src/ssn/app/services/action_log.py").read_text()


def test_module_contains_only_create_and_insert_sql():
    upper = SRC.upper()
    for forbidden in ("UPDATE ", "DELETE ", "DROP ", "ALTER "):
        assert forbidden not in upper, forbidden
    assert "CREATE TABLE IF NOT EXISTS" in upper and "INSERT INTO" in upper


def test_append_requires_acknowledgement_and_is_append_only(tmp_path):
    log = ActionLog(tmp_path / "a.sqlite")
    with pytest.raises(ValueError, match="acknowledgement"):
        log.append(
            record_id="R1",
            model_version="1.0.0",
            score=0.9,
            band="top",
            acknowledged=False,
            decision="record",
            action="outreach_email",
            reason=None,
        )
    assert log.append(
        record_id="R1",
        model_version="1.0.0",
        score=0.9,
        band="top",
        acknowledged=True,
        decision="record",
        action="outreach_email",
        reason="x",
    )
    assert log.append(
        record_id="R1",
        model_version="1.0.0",
        score=0.9,
        band="top",
        acknowledged=True,
        decision="dismiss",
        action="no_action",
        reason=None,
    )
    rows = log.rows()
    assert len(rows) == 2 and [r["decision"] for r in rows] == [
        "record",
        "dismiss",
    ]  # second entry appended, not overwritten
    assert set(rows[0]) >= {
        "logged_at_utc",
        "record_id",
        "model_version",
        "score",
        "band",
        "acknowledged",
        "decision",
        "action",
        "reason",
        "session_id",
    }
    assert "Target" not in rows[0] and "is_dropout" not in rows[0]


def test_invalid_decision_or_action_rejected(tmp_path):
    log = ActionLog(tmp_path / "a.sqlite")
    with pytest.raises(ValueError):
        log.append(
            record_id="R1",
            model_version="1",
            score=0.5,
            band="b",
            acknowledged=True,
            decision="delete",
            action="no_action",
            reason=None,
        )
    with pytest.raises(ValueError):
        log.append(
            record_id="R1",
            model_version="1",
            score=0.5,
            band="b",
            acknowledged=True,
            decision="record",
            action="expel",
            reason=None,
        )


def test_unwritable_path_is_handled_not_raised(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    log = ActionLog(blocker / "nested" / "a.sqlite")  # parent is a file -> cannot create
    assert log.writable is False and log.last_error
    assert (
        log.append(
            record_id="R1",
            model_version="1",
            score=0.5,
            band="b",
            acknowledged=True,
            decision="record",
            action="no_action",
            reason=None,
        )
        is False
    )


def test_export_csv_and_count(tmp_path):
    log = ActionLog(tmp_path / "a.sqlite")
    log.append(
        record_id="R2",
        model_version="1",
        score=0.4,
        band="b",
        acknowledged=True,
        decision="override",
        action="meeting_offer",
        reason="my judgement",
    )
    out = log.export_csv(tmp_path / "export.csv")
    assert out.exists() and log.count() == 1 and "my judgement" in out.read_text()


def test_configured_log_path_is_gitignored():
    r = subprocess.run(
        ["git", "check-ignore", "-q", "data/local/actions.sqlite"], capture_output=True
    )
    assert r.returncode == 0
    r = subprocess.run(
        ["git", "check-ignore", "-q", "data/local/actions_export.csv"], capture_output=True
    )
    assert r.returncode == 0


def test_schema_matches_contract(tmp_path):
    ActionLog(tmp_path / "a.sqlite")
    cols = [
        r[1]
        for r in sqlite3.connect(tmp_path / "a.sqlite").execute(
            "PRAGMA table_info(support_actions)"
        )
    ]
    assert cols == [
        "id",
        "logged_at_utc",
        "record_id",
        "model_version",
        "score",
        "band",
        "acknowledged",
        "decision",
        "action",
        "reason",
        "session_id",
    ]
