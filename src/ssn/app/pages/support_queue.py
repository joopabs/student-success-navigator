from __future__ import annotations

from dash import Input, Output, dcc, html

from ssn.app.components.ack_modal import ACTION_LABELS, DECISION_STATUS
from ssn.app.components.disclaimer import banner
from ssn.app.components.record_card import top_factors_text
from ssn.app.services.prioritization import band_counts, top_k


def _retrospective(state, k: int) -> html.Div:
    """Aggregate, precomputed, RETROSPECTIVE statistics from the held-out evaluation. No per-record outcomes."""
    if state.test_k is None:
        return html.Div()
    t = state.test_k[state.test_k["capacity_k_illustrative"] == k]
    if t.empty:
        return html.Div()
    r = t.iloc[0]
    return html.Div(
        [
            html.Strong(
                "Retrospective evaluation of this list size (aggregate, from the held-out evaluation): "
            ),
            f"in the historical cohort, about {r['precision_at_k_measured']:.0%} of a top-{k} list were students who later "
            f"left, covering {r['recall_at_k_measured']:.0%} of all who later left. This describes the past cohort as a whole, "
            "not any individual on today's list.",
        ],
        className="note",
    )


def _status(entry: dict | None) -> html.Td:
    """What an adviser has already done with this record. Never an outcome, never a prediction."""
    if not entry:
        return html.Td("Not yet handled", className="muted status-cell")
    return html.Td(
        [
            html.Span(
                DECISION_STATUS.get(entry["decision"], entry["decision"]),
                className=f"status status-{entry['decision']}",
            ),
            html.Div(
                f"{ACTION_LABELS.get(entry['action'], entry['action'])} · {entry['logged_at_utc'][:10]}",
                className="muted status-detail",
            ),
        ],
        className="status-cell",
    )


def table(state, k: int, hide_handled: bool = False) -> html.Div:
    rows, notice = top_k(state.ranked, k)
    latest = state.action_log.latest_by_record()
    on_list = len(rows)
    handled = sum(1 for rid in rows["record_id"].astype(str) if rid in latest)
    if hide_handled:
        rows = rows[~rows["record_id"].astype(str).isin(latest)]
    header = html.Tr(
        [
            html.Th("#"),
            html.Th("Record"),
            html.Th("Score", className="num"),
            html.Th("Band"),
            html.Th("Main factors (neutral)"),
            html.Th("Status"),
            html.Th(""),
        ]
    )
    body = []
    for _, r in rows.iterrows():
        rid = r["record_id"]
        body.append(
            html.Tr(
                [
                    html.Td(int(r["rank"]), className="rank"),
                    html.Td(html.A(rid, href=f"/review/{rid}")),
                    html.Td(f"{r['score']:.2f}", className="num"),
                    html.Td(
                        html.Span(r["band"], className=f"band-{r['band'].split()[0].lower()}"),
                        className="band-cell",
                    ),
                    html.Td(html.Div(top_factors_text(state, rid), className="factors")),
                    _status(latest.get(str(rid))),
                    html.Td(
                        html.Button(
                            "Record action",
                            id={"type": "open-ack", "record": rid},
                            n_clicks=0,
                            className="btn small",
                        ),
                        className="action-cell",
                    ),
                ]
            )
        )
    return html.Div(
        [
            html.Div(notice, className="note") if notice else html.Div(),
            _retrospective(state, k),
            html.Div(
                [
                    html.Span(["Handled ", html.B(str(handled))], className="chip"),
                    html.Span(["Remaining ", html.B(str(on_list - handled))], className="chip"),
                    html.Span(["On this list ", html.B(str(on_list))], className="chip"),
                ],
                className="chips coverage",
            ),
            html.Div(
                html.Table([html.Thead(header), html.Tbody(body)], className="table"),
                className="card",
            ),
        ]
    )


def layout(state) -> html.Div:
    counts = band_counts(state.ranked, state.bundle.bands)
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Support Queue"),
                    html.P(
                        "Students ranked by support-priority score (highest first; ties by record id). Every row "
                        "links to a review page; recording an action requires your acknowledgement."
                    ),
                ],
                className="page-head",
            ),
            banner(state),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Outreach list size (illustrative)"),
                            dcc.Dropdown(
                                id="queue-k",
                                options=[
                                    {
                                        "label": f"{k} students ({k // state.per_week} weeks × {state.per_week}/week)",
                                        "value": k,
                                    }
                                    for k in state.k_options
                                ],
                                value=state.k_default,
                                clearable=False,
                                style={"width": "320px"},
                            ),
                        ],
                        className="field",
                    ),
                    html.Div(
                        dcc.Checklist(
                            id="queue-hide",
                            options=[{"label": " Hide records already handled", "value": "hide"}],
                            value=[],
                        ),
                        className="field toggle",
                    ),
                    html.Div(
                        [
                            html.Span([f"{name} ", html.B(str(n))], className="chip")
                            for name, n in counts.items()
                        ],
                        className="chips",
                        title="Band counts in the whole cohort",
                    ),
                ],
                className="toolbar",
            ),
            html.Div(id="queue-table", children=table(state, state.k_default)),
        ]
    )


def register_callbacks(app, state) -> None:
    @app.callback(
        Output("queue-table", "children"),
        Input("queue-k", "value"),
        Input("queue-hide", "value"),
        Input("ack-toast", "children"),
    )
    def update(k, hide, _saved):
        """Re-renders on list size, on the filter, and whenever an action is saved."""
        return table(state, int(k or state.k_default), hide_handled=bool(hide))
