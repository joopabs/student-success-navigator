"""Append-only local action log (contract: contracts/action-log.md). Git-ignored SQLite.

Only CREATE TABLE IF NOT EXISTS and INSERT statements exist in this module (tested). No student
identifiers, no outcome labels. Nothing here is ever read by training or evaluation code.
"""

from __future__ import annotations

import csv
import secrets
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DECISIONS = ("record", "dismiss", "override")
ACTIONS = ("outreach_email", "meeting_offer", "resource_share", "no_action")

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS support_actions (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  logged_at_utc TEXT    NOT NULL,
  record_id     TEXT    NOT NULL,
  model_version TEXT    NOT NULL,
  score         REAL    NOT NULL,
  band          TEXT    NOT NULL,
  acknowledged  INTEGER NOT NULL CHECK (acknowledged IN (0,1)),
  decision      TEXT    NOT NULL
                CHECK (decision IN ('record','dismiss','override')),
  action        TEXT    NOT NULL
                CHECK (action IN ('outreach_email','meeting_offer',
                                  'resource_share','no_action')),
  reason        TEXT,
  session_id    TEXT
)
"""
INSERT_SQL = (
    "INSERT INTO support_actions (logged_at_utc, record_id, model_version, score, band, "
    "acknowledged, decision, action, reason, session_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)


class ActionLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.session_id = secrets.token_hex(4)
        self.writable = True
        self.last_error: str | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.path) as con:
                con.execute(CREATE_SQL)
        except (OSError, sqlite3.Error) as exc:
            self.writable = False
            self.last_error = str(exc)

    def append(
        self,
        *,
        record_id: str,
        model_version: str,
        score: float,
        band: str,
        acknowledged: bool,
        decision: str,
        action: str,
        reason: str | None,
    ) -> bool:
        if not acknowledged:
            raise ValueError("human-review acknowledgement is required before recording an action")
        if decision not in DECISIONS or action not in ACTIONS:
            raise ValueError("invalid decision or action")
        if not self.writable:
            return False
        try:
            with sqlite3.connect(self.path) as con:
                con.execute(
                    INSERT_SQL,
                    (
                        datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        record_id,
                        model_version,
                        float(score),
                        band,
                        1,
                        decision,
                        action,
                        reason or None,
                        self.session_id,
                    ),
                )
            return True
        except (OSError, sqlite3.Error) as exc:
            self.writable = False
            self.last_error = str(exc)
            return False

    def count(self) -> int:
        if not self.path.is_file():
            return 0
        with sqlite3.connect(self.path) as con:
            return int(con.execute("SELECT COUNT(*) FROM support_actions").fetchone()[0])

    def rows(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        with sqlite3.connect(self.path) as con:
            con.row_factory = sqlite3.Row
            return [dict(r) for r in con.execute("SELECT * FROM support_actions ORDER BY id")]

    def export_csv(self, out: Path) -> Path:
        rows = self.rows()
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["id"])
            w.writeheader()
            w.writerows(rows)
        return out
