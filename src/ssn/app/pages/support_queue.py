from __future__ import annotations

from dash import Input, Output, dcc, html

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


def table(state, k: int) -> html.Div:
    rows, notice = top_k(state.ranked, k)
    header = html.Tr(
        [
            html.Th("#"),
            html.Th("Record"),
            html.Th("Score"),
            html.Th("Band"),
            html.Th("Main factors (neutral)"),
            html.Th(""),
        ]
    )
    body = []
    for _, r in rows.iterrows():
        rid = r["record_id"]
        body.append(
            html.Tr(
                [
                    html.Td(int(r["rank"])),
                    html.Td(html.A(rid, href=f"/review/{rid}")),
                    html.Td(f"{r['score']:.2f}"),
                    html.Td(r["band"], className=f"band-{r['band'].split()[0].lower()}"),
                    html.Td(top_factors_text(state, rid)),
                    html.Td(
                        html.Button(
                            "Record support action",
                            id={"type": "open-ack", "record": rid},
                            n_clicks=0,
                            className="btn small",
                        )
                    ),
                ]
            )
        )
    return html.Div(
        [
            html.Div(notice, className="note") if notice else html.Div(),
            _retrospective(state, k),
            html.Table([html.Thead(header), html.Tbody(body)], className="table"),
        ]
    )


def layout(state) -> html.Div:
    counts = band_counts(state.ranked, state.bundle.bands)
    return html.Div(
        [
            html.H2("Support Queue"),
            banner(state),
            html.P(
                "Students ranked by support-priority score (highest first; ties by record id). Choose the list size that "
                "matches the illustrative outreach capacity. Every row links to a review page; recording an action "
                "requires your acknowledgement."
            ),
            html.Div(
                [
                    html.Label("Capacity K (illustrative)"),
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
                        style={"width": "360px"},
                    ),
                ]
            ),
            html.P(
                "Band counts in the whole cohort: "
                + " · ".join(f"{name}: {n}" for name, n in counts.items()),
                className="muted",
            ),
            html.Div(id="queue-table", children=table(state, state.k_default)),
        ]
    )


def register_callbacks(app, state) -> None:
    @app.callback(Output("queue-table", "children"), Input("queue-k", "value"))
    def update(k):
        return table(state, int(k or state.k_default))
