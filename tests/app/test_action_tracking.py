"""Support actions recorded by an adviser must be visible back in the app.

The log was previously write-only: `ssn actions export` was the sole read path, so an adviser could
not see which records had already been handled and would contact the same student twice. These
cover the read side. The one thing that must stay true throughout: the log is read for adviser
status only, never by training or evaluation, so recording an action cannot influence the model.
"""

from __future__ import annotations

import pytest

from ssn.app.app import route
from ssn.app.pages.support_queue import table
from tests.app.conftest import render_json

OUTCOME_TOKENS = ["is_dropout", '"Target"', "Graduate", "Enrolled"]


@pytest.fixture()
def handled(fixture_state):
    """Record one action against each of the first two queue records."""
    ids = [str(r) for r in fixture_state.ranked.head(2)["record_id"]]
    for rid, decision in zip(ids, ("record", "dismiss"), strict=False):
        row = fixture_state.ranked_row(rid)
        fixture_state.action_log.append(
            record_id=rid,
            model_version="1.0.0",
            score=float(row["score"]),
            band=str(row["band"]),
            acknowledged=True,
            decision=decision,
            action="outreach_email",
            reason=None,
        )
    return ids


def test_latest_by_record_keeps_only_the_most_recent_entry(fixture_state):
    log = fixture_state.action_log
    for decision in ("record", "dismiss", "override"):
        log.append(
            record_id="R-latest",
            model_version="1.0.0",
            score=0.5,
            band="b",
            acknowledged=True,
            decision=decision,
            action="no_action",
            reason=None,
        )
    assert log.latest_by_record()["R-latest"]["decision"] == "override"
    assert [r["decision"] for r in log.rows_for("R-latest")][0] == "override"
    assert len(log.rows_for("R-latest")) == 3, "history is append-only, not overwritten"


def test_queue_shows_status_for_handled_records(fixture_state, handled):
    text = render_json(table(fixture_state, len(fixture_state.ranked)))
    assert "Action recorded" in text
    assert "Dismissed" in text
    assert "Not yet handled" in text, "unhandled records must still be distinguishable"


def test_hide_handled_removes_them_from_the_list(fixture_state, handled):
    shown = render_json(table(fixture_state, len(fixture_state.ranked), hide_handled=True))
    for rid in handled:
        assert rid not in shown, rid


def test_review_page_shows_the_record_history(fixture_state, handled):
    text = render_json(route(fixture_state, f"/review/{handled[0]}"))
    assert "Actions already recorded for this record" in text
    assert "cannot influence the model" in text


def test_tracking_surfaces_never_show_outcome_labels(fixture_state, handled):
    for path in ("/queue", f"/review/{handled[0]}"):
        text = render_json(route(fixture_state, path))
        for token in OUTCOME_TOKENS:
            assert token not in text, (path, token)
