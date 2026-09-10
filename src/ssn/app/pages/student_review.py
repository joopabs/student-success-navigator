from __future__ import annotations

from dash import html

from ssn.app.components.disclaimer import banner
from ssn.app.components.record_card import factor_list, feature_table


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
            html.H2(f"Student Review · record {record_id}"),
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
