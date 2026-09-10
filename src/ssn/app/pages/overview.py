from __future__ import annotations

from dash import html

from ssn.app.components.disclaimer import banner


def layout(state) -> html.Div:
    m = state.bundle.manifest
    ts, cv = m["test_summary"], m["cv_summary"]
    band_rows = [
        html.Tr([html.Td(b["name"]), html.Td(f"[{b['lower']:.3f}, {b['upper']:.3f}]")])
        for b in m["bands"]
    ]
    return html.Div(
        [
            html.H2("Student Success Navigator"),
            banner(state),
            html.P(
                "Purpose: help academic advisers prioritise voluntary, supportive outreach after the first semester by "
                "ranking a de-identified cohort with a support-priority score built only from enrollment-time and "
                "first-semester information."
            ),
            html.H3("Intended use and non-use"),
            html.Ul(
                [
                    html.Li(m["intended_use"]),
                    html.Li(m["non_use"]),
                    html.Li(
                        "Sensitive attributes (gender, age, nationality, marital status, international status, special "
                        "needs) are never model inputs and never shown as reasons; they are used only in the aggregate "
                        "Equity Dashboard."
                    ),
                ]
            ),
            html.H3("Model and evaluated metrics (measured; held-out cohort evaluated once)"),
            html.Table(
                [
                    html.Tbody(
                        [
                            html.Tr([html.Td("Model version"), html.Td(m["model_version"])]),
                            html.Tr(
                                [
                                    html.Td("Estimator"),
                                    html.Td(
                                        m["estimator"]["class"].split(".")[-1]
                                        + (
                                            " + isotonic calibration"
                                            if m["calibration"]["applied"]
                                            else ""
                                        )
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td("Held-out PR-AUC"),
                                    html.Td(
                                        f"{ts['pr_auc']:.3f} (cross-validation {cv['pr_auc']:.3f} ± {cv['pr_auc_std_cv']:.3f})"
                                    ),
                                ]
                            ),
                            html.Tr([html.Td("Held-out ROC-AUC"), html.Td(f"{ts['roc_auc']:.3f}")]),
                            html.Tr(
                                [
                                    html.Td(
                                        f"Precision@K (K = {ts.get('k_applied_to_test', state.k_default)})"
                                    ),
                                    html.Td(f"{ts['precision_at_k']:.2f}"),
                                ]
                            ),
                            html.Tr(
                                [html.Td("Calibration error (ECE)"), html.Td(f"{ts['ece']:.3f}")]
                            ),
                            html.Tr(
                                [
                                    html.Td("Held-out evaluations"),
                                    html.Td(str(m["test_evaluations"])),
                                ]
                            ),
                        ]
                    )
                ],
                className="table",
            ),
            html.H3("Cohort and capacity"),
            html.P(
                f"Demo cohort: {len(state.cohort)} de-identified records with synthetic ids. Illustrative capacity: "
                f"{state.per_week} conversations per week × {state.window_weeks} weeks = {state.k_default} students "
                f"(other windows: {', '.join(str(k) for k in state.k_options)})."
            ),
            html.H3("Support bands (score ranges fixed in the model manifest)"),
            html.Table(
                [
                    html.Thead(html.Tr([html.Th("Band"), html.Th("Score range")])),
                    html.Tbody(band_rows),
                ],
                className="table",
            ),
            html.P(m["measured_vs_illustrative"], className="muted"),
        ]
    )
