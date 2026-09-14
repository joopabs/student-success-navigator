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
/* Design system shared with the business deck (reports/decks/canvas) and the report PDF:
   same palette, same Georgia display face, same reserved meaning for amber (assumptions). */
:root{
  --ink:#1d2a3a; --navy:#1f3a5f; --navy-deep:#16273f; --muted:#5b6b7b;
  --rule:#d8dee6; --pale:#e6eaef; --panel:#eef1f5; --paper:#fafbfc; --white:#fff;
  --amber:#b7791f; --amber-bg:#fff7e6; --amber-line:#e0a800; --amber-ink:#7d5210;
  --green:#2f6f4f; --blue:#4c72b0; --alert:#a33;
  --display:Georgia,"Iowan Old Style","Times New Roman",serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --lift:0 1px 2px rgba(29,42,58,.05),0 10px 28px -14px rgba(29,42,58,.22);
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:16px;line-height:1.55;-webkit-font-smoothing:antialiased}

/* Header */
.nav{display:flex;align-items:stretch;flex-wrap:wrap;gap:1.75rem;padding:0 2rem;background:var(--navy);border-bottom:3px solid var(--amber-line)}
.brand{display:flex;align-items:center;font-family:var(--display);font-size:1.12rem;font-weight:600;letter-spacing:-.01em;color:#fff;padding:1.05rem 0}
.navlinks{display:flex;flex-wrap:wrap;gap:.15rem}
.navlink{display:flex;align-items:center;color:#b9c7d9;text-decoration:none;font-weight:600;font-size:.85rem;padding:0 .85rem;border-bottom:3px solid transparent;margin-bottom:-3px;transition:color .15s ease,border-color .15s ease}
.navlink:hover{color:#fff;border-bottom-color:var(--amber-line)}

/* Page shell and type scale */
.wrap{max-width:1180px;margin:0 auto;padding:2.5rem 2rem 1rem}
.wrap>h2:first-child,.wrap>div>h2:first-child{margin-top:0}
.wrap h2{font-family:var(--display);font-size:2.05rem;line-height:1.16;letter-spacing:-.015em;font-weight:600;color:var(--navy);margin:0 0 .6rem}
.wrap h3{font-family:var(--display);font-size:1.32rem;font-weight:600;color:var(--navy);margin:2.25rem 0 .7rem}
.wrap h4{font-size:.95rem;font-weight:700;color:var(--navy);margin:1.5rem 0 .4rem}
.wrap p{margin:.6rem 0}
.wrap a{color:var(--blue);text-underline-offset:2px;text-decoration-color:rgba(76,114,176,.45)}

/* Callouts: amber marks an assumption, blue marks a note. Same meaning as in the deck. */
.disclaimer,.note{border-radius:0 10px 10px 0;padding:.9rem 1.15rem;margin:1.15rem 0;font-size:.9rem;line-height:1.5}
.disclaimer{background:var(--amber-bg);border:1px solid #f1ddb4;border-left:4px solid var(--amber-line);color:var(--amber-ink)}
.note{background:#eef4fb;border:1px solid #d7e3f4;border-left:4px solid var(--blue)}

/* Stat cards */
.kpis{display:flex;gap:1rem;flex-wrap:wrap;margin:1.5rem 0}
.kpi{flex:1;min-width:190px;background:var(--white);border:1px solid var(--rule);border-radius:12px;padding:1.15rem 1.35rem;box-shadow:var(--lift)}
.kpi h1{font-family:var(--display);font-size:2.45rem;line-height:1;font-weight:600;color:var(--navy);margin:.2rem 0 .25rem;font-variant-numeric:tabular-nums}
.kpi .muted{font-size:.74rem;letter-spacing:.09em;text-transform:uppercase;font-weight:700}

/* Tables: hairline rows, not a grid */
.table{border-collapse:collapse;width:100%;font-size:.9rem;margin:1.1rem 0;font-variant-numeric:tabular-nums}
.table th{text-align:left;font-size:.7rem;letter-spacing:.09em;text-transform:uppercase;font-weight:700;color:var(--muted);background:none;border:none;border-bottom:2px solid var(--navy);padding:0 1rem .6rem 0}
.table td{border:none;border-bottom:1px solid var(--pale);padding:.7rem 1rem .7rem 0;vertical-align:top}
.table tbody tr{transition:background .12s ease}
.table tbody tr:hover td{background:#f1f5f9}
.table td a{font-family:var(--mono);font-size:.86rem;font-weight:600}

/* Support bands: ordered by prominence, never by alarm. A student is not a hazard.
   The pill must sit on a span inside the cell - a td cannot be inline-block without
   dropping out of the table layout and overlapping the next column. */
.band-cell{white-space:nowrap;padding-right:1.25rem}
.band-priority,.band-check-in,.band-standard{display:inline-block;font-size:.73rem;font-weight:700;letter-spacing:.02em;padding:.28rem .7rem;border-radius:999px;white-space:nowrap}
.band-priority{background:#fbeaea;color:#9a2d2d;box-shadow:inset 0 0 0 1px #edc9c9}
.band-check-in{background:#fdf0d9;color:#8a5a00;box-shadow:inset 0 0 0 1px #eed9ab}
.band-standard{background:#e8f2ec;color:#2f6f4f;box-shadow:inset 0 0 0 1px #c9e0d3}

/* Controls */
.btn{font:inherit;font-size:.875rem;font-weight:600;padding:.5rem 1.05rem;border:1px solid var(--navy);background:var(--white);color:var(--navy);border-radius:8px;cursor:pointer;transition:background .15s ease,box-shadow .15s ease}
.btn:hover:not(:disabled){background:var(--panel)}
.btn.primary{background:var(--navy);color:#fff;box-shadow:var(--lift)}
.btn.primary:hover:not(:disabled){background:var(--navy-deep)}
.btn.small{font-size:.78rem;padding:.34rem .7rem}
.btn:disabled{opacity:.4;cursor:not-allowed;box-shadow:none}
.field label{display:block;font-size:.72rem;letter-spacing:.07em;text-transform:uppercase;font-weight:700;color:var(--muted);margin-bottom:.3rem}
.field input,.field select{font:inherit;font-size:.9rem;width:100%;padding:.5rem .7rem;border:1px solid var(--rule);border-radius:8px;background:var(--white);color:var(--ink)}
.field input:focus,.field select:focus{outline:3px solid rgba(76,114,176,.28);outline-offset:0;border-color:var(--blue)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:1rem 1.25rem}

/* Acknowledgement modal */
.modal{position:fixed;inset:0;background:rgba(16,26,40,.55);display:flex;align-items:center;justify-content:center;padding:1.5rem;z-index:50}
.modal.hidden{display:none}
.modal-body{background:var(--white);padding:1.8rem 2rem;border-radius:14px;max-width:660px;width:100%;max-height:88vh;overflow:auto;box-shadow:0 26px 64px -22px rgba(16,26,40,.5)}
.modal-body h3{font-family:var(--display);font-size:1.4rem;color:var(--navy);margin:0 0 .5rem}

/* Model Card page: dcc.Markdown had no styling at all before. */
.markdown{font-size:.94rem;line-height:1.65}
.markdown h1{font-family:var(--display);font-size:1.8rem;font-weight:600;color:var(--navy);margin:0 0 .6rem}
.markdown h2{font-family:var(--display);font-size:1.3rem;font-weight:600;color:var(--navy);margin:2rem 0 .6rem;padding-bottom:.35rem;border-bottom:1px solid var(--rule)}
.markdown h3{font-size:1rem;font-weight:700;color:var(--navy);margin:1.4rem 0 .35rem}
.markdown table{border-collapse:collapse;width:100%;font-size:.84rem;margin:1rem 0;font-variant-numeric:tabular-nums}
.markdown th{text-align:left;font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);border-bottom:2px solid var(--navy);padding:0 .85rem .5rem 0}
.markdown td{border-bottom:1px solid var(--pale);padding:.55rem .85rem .55rem 0}
.markdown code{font-family:var(--mono);font-size:.86em;background:var(--panel);padding:.1rem .35rem;border-radius:4px}
.markdown blockquote{margin:1.1rem 0;padding:.8rem 1.15rem;background:var(--amber-bg);border-left:4px solid var(--amber-line);border-radius:0 10px 10px 0;color:var(--amber-ink)}
.markdown ul,.markdown ol{padding-left:1.25rem}
.markdown li{margin:.3rem 0}

/* Utilities */
.muted{color:var(--muted);font-size:.86rem}
.warn{color:var(--alert);font-weight:600}
.errors{color:var(--alert);font-weight:600;margin:.75rem 0}
.factors li{margin:.45rem 0}
.toast{margin-top:.75rem;font-weight:600;color:var(--green)}
.footer{background:var(--white);border-top:1px solid var(--rule);margin-top:3rem;padding:1.5rem 2rem;color:var(--muted);font-family:var(--mono);font-size:.78rem;line-height:1.7}

@media (max-width:720px){
  .nav{padding:0 1rem;gap:.75rem}
  .wrap{padding:1.75rem 1.15rem 1rem}
  .wrap h2{font-size:1.6rem}
}
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
