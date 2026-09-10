"""Disclaimer banner and footer shown on every page."""

from __future__ import annotations

from dash import html


def banner(state) -> html.Div:
    return html.Div(
        [
            html.Strong("Advisory only. "),
            state.disclaimer,
            html.Span(
                f" Capacity ({state.per_week} per week × {state.window_weeks} weeks) is an illustrative assumption.",
                className="muted",
            ),
        ],
        className="disclaimer",
    )


def footer(state) -> html.Footer:
    m = state.bundle.manifest if state.bundle else {}
    version = m.get("model_version", "n/a")
    built = m.get("created_at", "n/a")
    sha = (m.get("pipeline_sha256") or "")[:12]
    return html.Footer(
        [
            html.Span(f"Model version {version}"),
            html.Span(f" · built {built}"),
            html.Span(f" · pipeline sha256 {sha}…" if sha else ""),
            html.Span(" · UCI dataset 697 (CC BY 4.0), one institution, historical data"),
        ],
        className="footer muted",
    )


def nav() -> html.Nav:
    links = [
        ("Overview", "/"),
        ("Support Queue", "/queue"),
        ("New Record Scoring", "/score"),
        ("Equity Dashboard", "/equity"),
        ("Model Card", "/model-card"),
    ]
    return html.Nav(
        [html.A(name, href=href, className="navlink") for name, href in links], className="nav"
    )
