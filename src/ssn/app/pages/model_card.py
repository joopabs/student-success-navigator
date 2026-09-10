from __future__ import annotations

from dash import dcc, html

from ssn.app.components.disclaimer import banner

GOVERNANCE = """
## Monitoring, human oversight and rollback (operational guidance)

**Prediction timing.** Scores are computed once per cohort at the end of the first semester from enrollment-time and
first-semester inputs only; nothing later is used.

**Privacy.** The app serves a de-identified demo cohort keyed by synthetic ids. Outcome labels and sensitive attributes
live in an evaluator-only file the app never opens (enforced by tests). The local action log stores synthetic ids,
scores, bands, decisions and optional free-text reasons; it is Git-ignored and never fed back into the model.

**Human oversight.** Every suggestion is advisory. Advisers review each record, may dismiss or override, and must
acknowledge that the decision is theirs before anything is logged. No automated or adverse action exists in the system.

**Monitoring (plan).** Each outreach cycle: compare the score distribution and band shares against the manifest's
out-of-fold shares; compare list composition by gender and age band against the audit baselines in
`reports/fairness/group_metrics.json`; review the Equity Dashboard; record any drift in the deployment log.

**Rollback.** The app refuses to start if the manifest version or pipeline checksum does not match. To roll back,
restore the previous `models/manifest.json` and pipeline file (or re-run `make final` at the previous commit) and set
`app.expected_model_version` in `configs/base.yaml` accordingly. See `docs/DEPLOYMENT.md` and `docs/MLOPS.md`.
"""


def layout(state) -> html.Div:
    return html.Div(
        [
            html.H2("Model Card"),
            banner(state),
            dcc.Markdown(state.model_card_md, className="markdown"),
            dcc.Markdown(GOVERNANCE, className="markdown"),
        ]
    )
