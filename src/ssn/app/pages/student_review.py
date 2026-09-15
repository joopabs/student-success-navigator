from __future__ import annotations

from dash import html

from ssn.app.components.ack_modal import ACTION_LABELS, DECISION_STATUS
from ssn.app.components.disclaimer import banner
from ssn.app.components.record_card import factor_list, feature_table


def _history(state, record_id: str) -> list:
    """Actions an adviser has already recorded against this record, most recent first."""
    rows = state.action_log.rows_for(record_id)
    if not rows:
        return []
    items = [
        html.Li(
            [
                html.Strong(DECISION_STATUS.get(r["decision"], r["decision"])),
                f" · {ACTION_LABELS.get(r['action'], r['action'])} · {r['logged_at_utc']}",
                html.Div(r["reason"], className="muted") if r["reason"] else html.Div(),
            ]
        )
        for r in rows
    ]
    return [
        html.H3("Actions already recorded for this record"),
        html.Ul(items, className="factors"),
        html.P(
            "Kept locally on this machine. Never read by training or evaluation, so recording an "
            "action cannot influence the model.",
            className="muted",
        ),
    ]


def layout(state, record_id: str) -> html.Div:
    row = state.ranked_row(record_id)
    if row is None:
        return html.Div(
            [
                html.H2("Student Review"),
                html.P(f"No record with id {record_id!r} in the demo cohort."),
                html.A("Back to queue", href="/queue"),
            ]
        )
    m = state.bundle.manifest
    ece = m["test_summary"].get("ece")
    return html.Div(
        [
            html.Div(
                [html.H2(f"Student Review · record {record_id}")], className="page-head"
            ),
            banner(state),
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("Support-priority score", className="muted"),
                            html.H1(f"{row['score']:.2f}"),
                        ],
                        className="kpi",
                    ),
                    html.Div(
                        [html.Span("Band", className="muted"), html.H1(row["band"])],
                        className="kpi",
                    ),
                    html.Div(
                        [
                            html.Span("Rank in cohort", className="muted"),
                            html.H1(f"{int(row['rank'])} / {len(state.ranked)}"),
                        ],
                        className="kpi",
                    ),
                ],
                className="kpis",
            ),
            html.H3("Main factors behind this score (neutral, academic)"),
            factor_list(state, record_id),
            html.Div(
                [
                    html.Strong("How certain is this? "),
                    "The score is a calibrated estimate from one institution's historical data",
                    f" (held-out calibration error {ece:.3f})." if ece is not None else ".",
                    f" Scores near the band boundary ({state.bundle.threshold:.3f}) are the least certain. The score says how the first "
                    "semester went compared with past students; it does not say what this student will do, and it is not a reason "
                    "to withhold anything.",
                ],
                className="note",
            ),
            *_history(state, record_id),
            html.H3("Inputs used (enrollment-time and first-semester only)"),
            feature_table(state, record_id),
            html.Button(
                "Record support action",
                id={"type": "open-ack", "record": record_id},
                n_clicks=0,
                className="btn primary",
            ),
            html.Span(
                " You will be asked to acknowledge that the suggestion is advisory before anything is saved.",
                className="muted",
            ),
            html.P(html.A("Back to queue", href="/queue")),
        ]
    )
