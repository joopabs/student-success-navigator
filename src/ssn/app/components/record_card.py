"""Neutral factor list and feature-value table for one de-identified record."""

from __future__ import annotations

from dash import html

from ssn.app.services.explanations import contributions, phrases, with_engineered


def factor_list(state, record_id: str, top: int = 5) -> html.Div:
    if state.shap is None:
        return html.Div(
            "Explanations are not available (run `python -m ssn explain`).", className="muted"
        )
    row = state.shap.row(record_id)
    if row is None:
        return html.Div("No precomputed explanation for this record.", className="muted")
    rec = state.record(record_id)
    values = (
        with_engineered(rec.drop(labels=["record_id"]).to_frame().T) if rec is not None else None
    )
    items = phrases(contributions(row, values), state.rules, state.reference, top=top)
    if not items:
        return html.Div("No factors to show.", className="muted")
    return html.Ul(
        [
            html.Li(
                [
                    html.Strong(f"{it['label']}: "),
                    it["phrase"],
                    html.Span(f" ({it['direction']})", className="muted"),
                ]
            )
            for it in items
        ],
        className="factors",
    )


def top_factors_text(state, record_id: str, n: int = 2) -> str:
    if state.shap is None:
        return ""
    row = state.shap.row(record_id)
    if row is None:
        return ""
    rec = state.record(record_id)
    values = (
        with_engineered(rec.drop(labels=["record_id"]).to_frame().T) if rec is not None else None
    )
    items = phrases(contributions(row, values), state.rules, state.reference, top=n)
    return "; ".join(it["phrase"] for it in items)


def feature_table(state, record_id: str) -> html.Table:
    rec = state.record(record_id)
    rows = []
    for f in state.fields:
        raw = rec[f.name]
        if f.options:
            label = dict(f.options).get(int(raw), str(raw))
            shown = f"{label} (code {int(raw)})"
        else:
            shown = f"{raw:g}" if isinstance(raw, (int, float)) else str(raw)
        rows.append(
            html.Tr([html.Td(f.label), html.Td(shown), html.Td(f.availability.replace("_", " "))])
        )
    return html.Table(
        [
            html.Thead(html.Tr([html.Th("Input"), html.Th("Value"), html.Th("Available at")])),
            html.Tbody(rows),
        ],
        className="table",
    )
