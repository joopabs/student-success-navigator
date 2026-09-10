"""SC-006: queue -> acknowledged saved action in at most three interactions (callback-level)."""

from __future__ import annotations

import json

from dash._callback_context import context_value
from dash._utils import AttributeDict

from ssn.app.app import create_app

KEY = (
    "..ack-modal.className...ack-selected.data...ack-record-summary.children"
    "...ack-check.value...ack-toast.children.."
)


def _run(app, output_key, inputs, triggered_id, *args):
    cb = app.callback_map[output_key]["callback"].__wrapped__
    context_value.set(
        AttributeDict(
            triggered_inputs=[
                {
                    "prop_id": json.dumps(triggered_id) + ".n_clicks"
                    if isinstance(triggered_id, dict)
                    else f"{triggered_id}.n_clicks",
                    "value": 1,
                }
            ]
        )
    )
    return cb(*args)


def test_three_interactions_from_queue_to_saved_action(fixture_state):
    app = create_app(fixture_state.cfg, state=fixture_state)
    rid = fixture_state.ranked.iloc[0]["record_id"]
    key = KEY
    before = fixture_state.action_log.count()
    # 1) click "Record support action" on the queue row -> modal opens with the record selected
    out = _run(
        app,
        key,
        None,
        {"type": "open-ack", "record": rid},
        [1],
        0,
        0,
        None,
        [],
        "record",
        "outreach_email",
        None,
    )
    assert out[0] == "modal" and out[1] == rid
    # 2) tick the acknowledgement box -> Save becomes enabled
    enable = app.callback_map["ack-save.disabled"]["callback"].__wrapped__
    assert enable(["ack"]) is False and enable([]) is True
    # 3) click Save -> entry appended, modal closes
    out = _run(
        app, key, None, "ack-save", [1], 0, 1, rid, ["ack"], "record", "outreach_email", "follow-up"
    )
    assert out[0] == "modal hidden" and "Saved locally" in out[4]
    assert fixture_state.action_log.count() == before + 1
    rows = fixture_state.action_log.rows()
    assert (
        rows[-1]["record_id"] == rid
        and rows[-1]["acknowledged"] == 1
        and rows[-1]["decision"] == "record"
    )


def test_save_without_acknowledgement_writes_nothing(fixture_state):
    app = create_app(fixture_state.cfg, state=fixture_state)
    rid = fixture_state.ranked.iloc[1]["record_id"]
    key = KEY
    before = fixture_state.action_log.count()
    out = _run(app, key, None, "ack-save", [0], 0, 1, rid, [], "record", "outreach_email", None)
    assert "Tick the acknowledgement" in out[4] and fixture_state.action_log.count() == before
