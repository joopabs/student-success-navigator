from __future__ import annotations

from dash import ALL, Input, Output, State, dcc, html

from ssn.app.components.disclaimer import banner
from ssn.app.services.explanations import (
    contributions,
    explain_hypothetical,
    phrases,
    with_engineered,
)
from ssn.app.services.inference import score_frame
from ssn.app.services.validation import validate
from ssn.modeling.threshold import assign_band


def _meaning(state, f) -> str:
    """What this field is, and what entering a higher value means.

    Both halves are sourced, not written here: the definition is the source dataset's own wording
    carried on the allow-list, and the direction is the adviser phrasing in configs/language.yaml -
    the same wording the Student Review explanations use, so the form and the explanations agree.

    Coded fields are skipped: their dropdown already shows decoded labels, their descriptions are
    raw code lists, and "higher" is not meaningful for a category code.
    """
    if f.options:
        return ""
    parts = []
    described = " ".join((f.description or "").split())
    # skip a description that only restates the label
    if described and described.lower().rstrip(".").replace(f.label.lower(), "").strip(" ()0123456789-–"):
        parts.append(described.rstrip(".") + ".")
    phrase = (state.rules.features.get(f.name) or {}).get("higher_phrase")
    if phrase:
        parts.append(f"Higher: {phrase}.")
    return " ".join(parts)


def _hint(state, f) -> html.Div:
    """Accepted range, the range actually seen in training, and the training median."""
    if f.options:
        return html.Div()
    parts = []
    if f.lo is not None and f.hi is not None:
        parts.append(f"accepts {f.lo:g}-{f.hi:g}")
    seen = (state.observed_ranges or {}).get(f.name)
    if seen and (f.lo, f.hi) != (seen["min"], seen["max"]):
        # only worth saying when real values occupy a narrower band than the scale allows
        parts.append(f"training data {seen['min']:g}-{seen['max']:g}")
    typical = (state.reference or {}).get(f.name)
    if typical is not None:
        parts.append(f"typical {typical:.4g}")
    return html.Div(" · ".join(parts), className="field-hint") if parts else html.Div()


def _input(f):
    if f.options:
        return dcc.Dropdown(
            id={"type": "nr-field", "name": f.name},
            options=[{"label": f"{lbl} ({code})", "value": code} for code, lbl in f.options],
            placeholder="choose",
            clearable=True,
        )
    return dcc.Input(
        id={"type": "nr-field", "name": f.name},
        type="number",
        placeholder=f"{f.lo:g} to {f.hi:g}" if f.lo is not None else "number",
        min=f.lo,
        max=f.hi,
        step="any",
        debounce=True,
        style={"width": "100%"},
    )


def layout(state) -> html.Div:
    groups = {"enrollment": [], "first_semester": []}
    for f in state.fields:
        groups.setdefault(f.availability, []).append(f)

    def section(title, fields):
        return html.Div(
            [
                html.H4(title),
                html.Div(
                    [
                        html.Div(
                            [
                                    html.Label(f.label),
                                    _input(f),
                                    html.Div(_meaning(state, f), className="field-meaning")
                                    if _meaning(state, f)
                                    else html.Div(),
                                    _hint(state, f),
                                ],
                            className="field",
                        )
                        for f in fields
                    ],
                    className="grid",
                ),
            ],
            className="card pad",
        )

    return html.Div(
        [
            html.Div(
                [
                    html.H2("New Record Scoring (hypothetical)"),
                    html.P(
                        "Enter a hypothetical first-semester situation. Only the final model's inputs are accepted: "
                        "enrollment-time details and first-semester results. There are no second-semester, outcome, "
                        "or sensitive-attribute fields. Under each box: what the field means, which way a higher "
                        "value points, and the range and typical value seen in the training data."
                    ),
                ],
                className="page-head",
            ),
            banner(state),
            section("Known at enrollment", groups.get("enrollment", [])),
            section("Known by the end of the first semester", groups.get("first_semester", [])),
            html.Button(
                "Score hypothetical record", id="nr-submit", n_clicks=0, className="btn primary"
            ),
            html.Div(id="nr-errors", className="errors"),
            html.Div(id="nr-result"),
        ]
    )


def register_callbacks(app, state) -> None:
    @app.callback(
        Output("nr-errors", "children"),
        Output("nr-result", "children"),
        Input("nr-submit", "n_clicks"),
        State({"type": "nr-field", "name": ALL}, "value"),
        State({"type": "nr-field", "name": ALL}, "id"),
        prevent_initial_call=True,
    )
    def score(n, values, ids):
        form = {i["name"]: v for i, v in zip(ids, values, strict=False)}
        errors, frame = validate(form, state.fields)
        if errors:
            return html.Ul([html.Li(msg) for msg in errors.values()]), html.Div()
        s = float(score_frame(state.bundle, frame)[0])
        band = assign_band(s, state.bundle.bands)
        try:
            shap_row = explain_hypothetical(state.bundle.pipeline, frame, state.cfg.seed)
            items = phrases(
                contributions(shap_row, with_engineered(frame)), state.rules, state.reference
            )
            factors = html.Ul(
                [
                    html.Li(
                        [
                            html.Strong(f"{it['label']}: "),
                            it["phrase"],
                            html.Span(f" ({it['direction']})", className="muted"),
                        ]
                    )
                    for it in items
                ]
            )
        except Exception as exc:  # noqa: BLE001 - explanation failure must not hide the score
            factors = html.Div(f"Explanation unavailable: {exc}", className="muted")
        return html.Div(), html.Div(
            [
                html.H3("Result for this HYPOTHETICAL record"),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span("Support-priority score", className="muted"),
                                html.H1(f"{s:.2f}"),
                            ],
                            className="kpi",
                        ),
                        html.Div(
                            [html.Span("Band", className="muted"), html.H1(band)], className="kpi"
                        ),
                    ],
                    className="kpis",
                ),
                html.H4("Main factors (neutral, academic)"),
                factors,
                html.P(
                    "Hypothetical input; nothing is stored. The score is advisory and not a prediction about any real student.",
                    className="note",
                ),
            ]
        )
