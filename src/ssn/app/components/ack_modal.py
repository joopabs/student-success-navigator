"""Human-review acknowledgement modal shared by the Support Queue and Student Review pages.

Save is disabled until the acknowledgement box is ticked. Dismiss and override are also logged.
The log is append-only, local, and Git-ignored.
"""

from __future__ import annotations

from dash import ALL, Input, Output, State, ctx, dcc, html, no_update

from ssn.app.services.action_log import ACTIONS, DECISIONS

ACK_TEXT = (
    "I have reviewed this record myself. I understand the score is advisory, not a prediction about this "
    "student's future, and that the decision and any action are mine."
)
ACTION_LABELS = {
    "outreach_email": "Send a supportive check-in message",
    "meeting_offer": "Offer a meeting",
    "resource_share": "Share support resources",
    "no_action": "No action at this time",
}
DECISION_LABELS = {
    "record": "Record the suggested support action",
    "dismiss": "Dismiss the suggestion",
    "override": "Override with my own judgement",
}


def modal() -> html.Div:
    return html.Div(
        id="ack-modal",
        className="modal hidden",
        children=[
            html.Div(
                className="modal-body",
                children=[
                    html.H3("Record a support action"),
                    html.Div(id="ack-record-summary", className="muted"),
                    dcc.Checklist(
                        id="ack-check", options=[{"label": ACK_TEXT, "value": "ack"}], value=[]
                    ),
                    dcc.RadioItems(
                        id="ack-decision",
                        options=[{"label": DECISION_LABELS[d], "value": d} for d in DECISIONS],
                        value="record",
                    ),
                    dcc.Dropdown(
                        id="ack-action",
                        options=[{"label": ACTION_LABELS[a], "value": a} for a in ACTIONS],
                        value="outreach_email",
                        clearable=False,
                    ),
                    dcc.Textarea(
                        id="ack-reason",
                        placeholder="Optional reason (kept locally)",
                        style={"width": "100%"},
                    ),
                    html.Div(
                        [
                            html.Button(
                                "Save",
                                id="ack-save",
                                n_clicks=0,
                                disabled=True,
                                className="btn primary",
                            ),
                            html.Button("Cancel", id="ack-cancel", n_clicks=0, className="btn"),
                        ]
                    ),
                    html.Div(id="ack-toast", className="toast"),
                ],
            ),
            dcc.Store(id="ack-selected"),
        ],
    )


def register_callbacks(app, state) -> None:
    @app.callback(
        Output("ack-modal", "className"),
        Output("ack-selected", "data"),
        Output("ack-record-summary", "children"),
        Output("ack-check", "value"),
        Output("ack-toast", "children"),
        Input({"type": "open-ack", "record": ALL}, "n_clicks"),
        Input("ack-cancel", "n_clicks"),
        Input("ack-save", "n_clicks"),
        State("ack-selected", "data"),
        State("ack-check", "value"),
        State("ack-decision", "value"),
        State("ack-action", "value"),
        State("ack-reason", "value"),
        prevent_initial_call=True,
    )
    def toggle(open_clicks, cancel, save, selected, ack, decision, action, reason):
        trig = ctx.triggered_id
        if isinstance(trig, dict) and trig.get("type") == "open-ack":
            rid = trig["record"]
            row = state.ranked_row(rid)
            summary = (
                f"Record {rid} · score {row['score']:.3f} · band {row['band']}"
                if row is not None
                else f"Record {rid}"
            )
            return "modal", rid, summary, [], ""
        if trig == "ack-cancel":
            return "modal hidden", None, "", [], ""
        if trig == "ack-save":
            if not selected or "ack" not in (ack or []):
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    "Tick the acknowledgement box to save.",
                )
            row = state.ranked_row(selected)
            ok = state.action_log.append(
                record_id=selected,
                model_version=state.bundle.model_version if state.bundle else "n/a",
                score=float(row["score"]) if row is not None else float("nan"),
                band=str(row["band"]) if row is not None else "n/a",
                acknowledged=True,
                decision=decision,
                action=action,
                reason=reason,
            )
            msg = (
                "Saved locally."
                if ok
                else f"Could not write the local log ({state.action_log.last_error}); scoring continues."
            )
            return "modal hidden", None, "", [], msg
        return no_update, no_update, no_update, no_update, no_update

    @app.callback(Output("ack-save", "disabled"), Input("ack-check", "value"))
    def enable_save(ack):
        return "ack" not in (ack or [])
