from __future__ import annotations

from dash import html

from ssn.app.components.disclaimer import banner

COLS = ["group", "n", "reliable", "base_rate", "selection_rate", "tpr", "fpr", "brier"]
HEAD = [
    "Group",
    "n",
    "Reliable (n ≥ min)",
    "Observed rate in cohort",
    "Selection rate",
    "TPR",
    "FPR",
    "Brier",
]


def _tbl(rows, attribute, op):
    body = []
    for r in rows:
        if r["attribute"] != attribute or r["operating_point"] != op:
            continue
        cells = []
        for c in COLS:
            v = r[c]
            if c == "reliable":
                cells.append(
                    html.Td(
                        "yes" if v else "NO — small group, treat as indicative",
                        className="" if v else "warn",
                    )
                )
            elif isinstance(v, float):
                cells.append(html.Td(f"{v:.3f}"))
            else:
                cells.append(html.Td(str(v)))
        body.append(html.Tr(cells))
    return html.Table(
        [html.Thead(html.Tr([html.Th(h) for h in HEAD])), html.Tbody(body)], className="table"
    )


def layout(state) -> html.Div:
    eq = state.equity
    if not eq:
        return html.Div(
            [
                html.H2("Equity Dashboard"),
                banner(state),
                html.P("Fairness audit not yet run (`python -m ssn fairness audit`)."),
            ]
        )
    summ = [s for s in eq["attribute_summary"] if s["operating_point"] == "threshold"]
    sections = []
    for attr in eq["attributes"]:
        s = next((x for x in summ if x["attribute"] == attr), None)
        sections += [
            html.H3(f"{attr.replace('_', ' ').title()} — at the deployed threshold"),
            html.P(
                (
                    f"Demographic-parity difference {s['dp_difference']:.3f} · disparate-impact ratio {s['di_ratio']:.2f} · "
                    f"equal-opportunity (TPR) difference {s['eo_difference']:.3f} · equalized-odds max difference {s['eq_odds_max_diff']:.3f} "
                    f"(reference group: {s['reference_group']}; reliable groups: {s['n_reliable_groups']}/{s['n_groups']})"
                )
                if s
                else "",
                className="muted",
            ),
            _tbl(eq["groups"], attr, "threshold"),
            html.H4(f"{attr.replace('_', ' ').title()} — at top-K (K = {eq['k']})"),
            _tbl(eq["groups"], attr, f"top_k={eq['k']}"),
        ]
    figs = [html.Img(src=src, style={"maxWidth": "100%"}) for src in eq["figures"].values() if src]
    return html.Div(
        [
            html.H2("Equity Dashboard"),
            banner(state),
            html.P(
                f"Aggregate fairness metrics of the deployed model on the held-out cohort (n = {eq['n']}), precomputed by "
                f"`python -m ssn fairness audit`. Gender encoding {eq['gender_encoding']} verified against the source "
                f"documentation: {eq['gender_encoding_verified']}. Groups with fewer than {eq['min_group_size']} records are "
                "flagged and should be read as indicative only. Nothing here is computed in the app, and none of these "
                "attributes is a model input or an adviser-facing reason."
            ),
            *sections,
            html.H3("Figures"),
            *figs,
            html.H3("Reading these numbers"),
            html.P(
                "Selection-rate gaps partly mirror differences in observed rates between groups; the equal-opportunity "
                "difference (TPR) shows whether students who later left had the same chance of appearing on the list. "
                "A large age-band TPR gap means younger students who leave are under-reached; the recommended response is an "
                "adviser-side rule (reserve part of the outreach list for first-years), not a change to the model. "
                "Metrics inside a tolerance do not establish fairness. Full analysis: reports/bias_fairness_analysis.md."
            ),
            html.H3("Mitigations tried (training data only; reported, not deployed unless marked)"),
            html.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th(c)
                                for c in [
                                    "variant",
                                    "deployable",
                                    "pr_auc",
                                    "recall_at_k",
                                    "gender_dp_difference",
                                    "gender_eo_difference",
                                    "age_band_eo_difference",
                                ]
                            ]
                        )
                    ),
                    html.Tbody(
                        [
                            html.Tr(
                                [
                                    html.Td(f"{r[c]:.4f}" if isinstance(r[c], float) else str(r[c]))
                                    for c in [
                                        "variant",
                                        "deployable",
                                        "pr_auc",
                                        "recall_at_k",
                                        "gender_dp_difference",
                                        "gender_eo_difference",
                                        "age_band_eo_difference",
                                    ]
                                ]
                            )
                            for r in eq["mitigation"]
                        ]
                    ),
                ],
                className="table",
            ),
            html.H3("Limitations"),
            html.P(
                "One institution's historical data; proxies (parental background, application route) can re-encode age and "
                "socioeconomic status; small-group metrics are noisy; outcomes may reflect past institutional support, not "
                "student potential.",
                className="muted",
            ),
        ]
    )
