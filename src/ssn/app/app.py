"""Student Success Navigator — Dash app factory.

Run: `python -m ssn app` (or `python -m ssn.app`). Loads the persisted pipeline once (no fitting),
scores the de-identified demo cohort, and serves six pages. If the artifact fails verification the
app serves a single blocking page and no scores.
"""

from __future__ import annotations

import logging

from dash import Dash, Input, Output, dcc, html

from ssn.app.components import ack_modal
from ssn.app.components.disclaimer import footer, nav
from ssn.app.pages import (
    equity_dashboard,
    model_card,
    new_record,
    overview,
    student_review,
    support_queue,
)
from ssn.app.state import AppState, load_state
from ssn.config import Config, load

log = logging.getLogger(__name__)

CSS = """
body{font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;margin:0;color:#1d2a3a;background:#fafbfc}
.wrap{max-width:1100px;margin:0 auto;padding:1rem 1.5rem}
.nav{display:flex;gap:1rem;padding:.75rem 1.5rem;background:#1f3a5f}.navlink{color:#fff;text-decoration:none;font-weight:600}
.disclaimer{background:#fff7e6;border-left:4px solid #e0a800;padding:.6rem .9rem;margin:.75rem 0;font-size:.92rem}
.note{background:#eef4fb;border-left:4px solid #4c72b0;padding:.6rem .9rem;margin:.75rem 0;font-size:.92rem}
.muted{color:#5b6b7b;font-size:.9rem}.warn{color:#a33;font-weight:600}
.table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.5rem 0}.table th,.table td{border:1px solid #d8dee6;padding:.35rem .5rem;text-align:left}
.table th{background:#eef1f5}.kpis{display:flex;gap:1.5rem}.kpi{background:#fff;border:1px solid #d8dee6;padding:.6rem 1rem;border-radius:6px}.kpi h1{margin:.1rem 0}
.btn{padding:.35rem .7rem;border:1px solid #1f3a5f;background:#fff;color:#1f3a5f;border-radius:4px;cursor:pointer}.btn.primary{background:#1f3a5f;color:#fff}
.btn.small{font-size:.8rem}.btn:disabled{opacity:.45;cursor:not-allowed}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center}
.modal.hidden{display:none}.modal-body{background:#fff;padding:1.2rem 1.5rem;border-radius:8px;max-width:620px;width:90%}
.footer{padding:1rem 1.5rem;border-top:1px solid #d8dee6;margin-top:2rem}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.6rem 1rem}
.field label{display:block;font-size:.85rem;margin-bottom:.15rem}.errors{color:#a33;margin:.5rem 0}.factors li{margin:.25rem 0}
.band-priority{color:#a33;font-weight:600}.band-check-in{color:#b7791f;font-weight:600}.band-standard{color:#2f6f4f}
.toast{margin-top:.5rem;font-weight:600}
"""


def blocked_layout(state: AppState) -> html.Div:
    return html.Div(
        [
            html.H2("Student Success Navigator is not serving scores"),
            html.Div(state.blocked_reason, className="disclaimer"),
            html.P(
                "Fix the artifact or configuration and restart. No scores, records, or explanations are shown while blocked."
            ),
            html.P(state.disclaimer, className="muted"),
        ],
        className="wrap",
    )


def route(state: AppState, pathname: str):
    if state.blocked:
        return blocked_layout(state)
    path = (pathname or "/").rstrip("/") or "/"
    if path == "/":
        return overview.layout(state)
    if path == "/queue":
        return support_queue.layout(state)
    if path.startswith("/review/"):
        return student_review.layout(state, path.split("/review/", 1)[1])
    if path == "/score":
        return new_record.layout(state)
    if path == "/equity":
        return equity_dashboard.layout(state)
    if path == "/model-card":
        return model_card.layout(state)
    return html.Div([html.H2("Not found"), html.A("Overview", href="/")])


def create_app(cfg: Config | None = None, state: AppState | None = None) -> Dash:
    cfg = cfg or load("configs/base.yaml", set_seeds=False)
    state = state or load_state(cfg)
    app = Dash(__name__, suppress_callback_exceptions=True, title="Student Success Navigator")
    app.index_string = app.index_string.replace("</head>", f"<style>{CSS}</style></head>")
    app.layout = html.Div(
        [
            nav(),
            dcc.Location(id="url", refresh=False),
            html.Div(id="page", className="wrap"),
            ack_modal.modal(),
            footer(state),
        ]
    )

    @app.callback(Output("page", "children"), Input("url", "pathname"))
    def render(pathname):
        return route(state, pathname)

    if not state.blocked:
        ack_modal.register_callbacks(app, state)
        support_queue.register_callbacks(app, state)
        new_record.register_callbacks(app, state)
    app.server.config["SSN_STATE"] = state  # for tests / inspection
    if state.blocked:
        log.error("app blocked: %s", state.blocked_reason)
    else:
        log.info("serving %d records, model %s", len(state.ranked), state.bundle.model_version)
    return app


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="ssn.app")
    p.add_argument("--config", default="configs/base.yaml")
    a = p.parse_args(argv)
    cfg = load(a.config, set_seeds=False)
    app = create_app(cfg)
    app.run(host=str(cfg.get("app.host")), port=int(cfg.get("app.port")), debug=False)
    return 0
