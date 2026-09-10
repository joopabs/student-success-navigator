"""Render reports/model_card.md from the manifest and computed results (T065).

Fails if any manifest placeholder remains (test not evaluated) or if the rendered text contains
the bare over-claim "the model is fair". Hand-written limitations come from reports/limitations.md.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


class ModelCardError(RuntimeError):
    pass


OVERCLAIMS = ("the model is fair", "the model is unbiased", "no bias")


def _md_table(df: pd.DataFrame, cols: list[str] | None = None, r: int = 4) -> str:
    cols = cols or list(df.columns)
    out = "| " + " | ".join(cols) + " |\n|" + "|".join("---" for _ in cols) + "|\n"
    for _, row in df.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            cells.append("" if pd.isna(v) else (f"{v:.{r}f}" if isinstance(v, float) else str(v)))
        out += "| " + " | ".join(cells) + " |\n"
    return out


def render(
    manifest: dict[str, Any],
    test_metrics: pd.DataFrame,
    test_k: pd.DataFrame,
    fairness: dict[str, Any] | None,
    limitations_md: str,
    explain_method: dict[str, Any] | None,
    out_path: Path,
) -> str:
    placeholders = [k for k, v in manifest["test_summary"].items() if v is None]
    if manifest.get("test_evaluations", 0) < 1 or placeholders:
        raise ModelCardError(
            f"manifest still has test placeholders {placeholders}; run `python -m ssn evaluate-test`"
        )
    t = test_metrics.iloc[0]
    thr = manifest["threshold"]
    bands = manifest["bands"]
    feats = manifest["features"]
    fair_block = "_Fairness audit not yet run._"
    if fairness:
        summ = pd.DataFrame(fairness["attribute_summary"])
        summ = summ[summ["operating_point"] == "threshold"]
        groups = pd.DataFrame(fairness["groups"])
        groups = groups[groups["operating_point"] == "threshold"]
        unreliable = groups[~groups["reliable"]]
        fair_block = (
            f"Audited on the held-out cohort (n = {fairness['n']}) by {', '.join(fairness['attributes'])}; gender encoding "
            f"{fairness['gender_encoding']} verified = {fairness['gender_encoding_verified']}. Groups with n < "
            f"{fairness['min_group_size']} are flagged unreliable"
            + (
                f" ({', '.join(f'{r.attribute}={r.group} n={r.n}' for r in unreliable.itertuples())})."
                if len(unreliable)
                else "."
            )
            + "\n\n"
            + _md_table(
                summ,
                [
                    "attribute",
                    "reference_group",
                    "n_reliable_groups",
                    "dp_difference",
                    "di_ratio",
                    "eo_difference",
                    "eq_odds_max_diff",
                ],
            )
            + "\n"
            + _md_table(
                groups,
                [
                    "attribute",
                    "group",
                    "n",
                    "reliable",
                    "base_rate",
                    "selection_rate",
                    "tpr",
                    "fpr",
                    "brier",
                ],
            )
            + "\nThese numbers describe observed disparities at the deployed operating point; they do not, by "
            "themselves, establish that the model treats groups fairly. Full discussion, mitigation results and "
            "residual risks: `reports/bias_fairness_analysis.md`."
        )
    exp = ""
    if explain_method:
        exp = (
            f"{explain_method.get('method')} on the {explain_method.get('ensemble_members')} calibrated ensemble members; "
            f"{explain_method.get('aggregation')}; explains {explain_method.get('explains')}. Outputs under "
            "`reports/explainability/`. Sensitive attributes are never shown as reasons."
        )
    text = (
        f"""# Model Card — Student Success Navigator support-priority model

**Version:** {manifest["model_version"]} · **Built:** {manifest["created_at"]} · **Git:** `{(manifest.get("git_sha") or "n/a")[:12]}` ·
**Rendered:** {datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")} by `python -m ssn model-card` · **Held-out evaluations:** {manifest["test_evaluations"]}

> {manifest["disclaimer"]}

## Intended use

{manifest["intended_use"]} The score ranks students for a **voluntary, supportive** adviser conversation
within a limited outreach capacity. It is decision support for qualified staff, reviewed case by case.

## Out-of-scope use (prohibited)

{manifest["non_use"]} The score is not a prediction about a student's ability or worth and must not be
shown to students as such.

## Data

- **Source:** {manifest["data"]["source"]}, DOI {manifest["data"]["doi"]}, licence {manifest["data"]["license"]};
  one higher-education institution; not representative of Philippine or other institutions.
- **Training / test:** {manifest["data"]["n_train"]} / {manifest["data"]["n_test"]} student records (positive rate
  {manifest["data"]["positive_rate_train"]} / {manifest["data"]["positive_rate_test"]}); stratified split, seed {manifest["seed"]}.
- **Target:** `{manifest["target"]["name"]}` = 1 where source Target = {manifest["target"]["positive_label"]}; {", ".join(manifest["target"]["negative_labels"])} = 0.
- **Inputs ({len(feats["allowlisted_source"])} source columns + {len(feats["engineered"])} engineered):** enrollment-time and first-semester
  information only. Excluded: {len(feats["prohibited_excluded"])} second-semester columns (after the prediction point),
  {len(feats["ambiguous_excluded"])} financial-status columns with undocumented timing ({", ".join(feats["ambiguous_excluded"])}), and
  {len(feats["sensitive_excluded_audit_only"])} sensitive attributes used for auditing only ({", ".join(feats["sensitive_excluded_audit_only"])}).

## Model

- **Estimator:** `{manifest["estimator"]["class"]}` inside a scikit-learn pipeline (median imputation, scaling,
  one-hot encoding, stateless first-semester feature engineering). Selection setting: {feats["selection_setting"] or "all features"}.
- **Imbalance:** {manifest["imbalance_treatment"]}.
- **Calibration:** {"applied (" + str(manifest["calibration"]["method"]) + ")" if manifest["calibration"]["applied"] else "not applied"}.
- **Selection rationale:** {manifest["selection_rationale"]}
- **Environment:** Python {manifest["python_version"]}; {", ".join(f"{k} {v}" for k, v in manifest["library_versions"].items())}.

## Operating point (illustrative capacity, measured behaviour)

Capacity assumption: **{thr["capacity_per_week"]} students per week over {thr["window_weeks"]} weeks = K {thr["capacity_k"]}** per cohort of
{thr["n_cohort_expected"]} (ILLUSTRATIVE). Rule `{thr["rule"]}` gives **threshold {thr["value"]:.4f}** (OOF selection rate {thr["selection_rate_oof"]:.4f}).

| Band | Score range | Rule |
|---|---|---|
"""
        + "\n".join(
            f"| {b['name']} | [{b['lower']:.4f}, {b['upper']:.4f}] | {b.get('rule', '')} |"
            for b in bands
        )
        + f"""

## Performance (measured)

Cross-validation on the training split: PR-AUC {manifest["cv_summary"]["pr_auc"]:.4f} ± {manifest["cv_summary"]["pr_auc_std_cv"]:.4f},
Recall@K {manifest["cv_summary"]["recall_at_k"]:.4f}, Brier {manifest["cv_summary"]["brier"]:.4f}, ECE {manifest["cv_summary"]["ece"]:.4f}.

Held-out test (single evaluation, n = {manifest["data"]["n_test"]}):

| PR-AUC | ROC-AUC | Recall@K | Precision@K | Brier | ECE | Precision at threshold | Recall at threshold |
|---|---|---|---|---|---|---|---|
| {t["pr_auc"]:.4f} | {t["roc_auc"]:.4f} | {t["recall_at_k"]:.4f} | {t["precision_at_k"]:.4f} | {t["brier"]:.4f} | {t["ece"]:.4f} | {t["precision_at_threshold"]:.4f} | {t["recall_at_threshold"]:.4f} |

Recall@K is bounded by capacity: K = {int(t["k"])} slots for {int(test_k["dropouts_in_test"].iloc[0])} eventual dropouts in the test cohort.
Capacity sensitivity (measured recall, illustrative windows):

{_md_table(test_k, ["window_weeks", "capacity_k_illustrative", "recall_at_k_measured", "precision_at_k_measured"])}
Zero predicted positives on test: {manifest.get("zero_predicted_positives_on_test")}.

## Explainability

{exp or "_Explainability outputs not yet generated._"}

## Fairness (aggregate audit)

{fair_block}

## Limitations, risks and human oversight

{limitations_md.strip()}

## Provenance

Config sha256 `{manifest["config_sha256"][:16]}…`, pipeline sha256 `{manifest["pipeline_sha256"][:16]}…`, raw data sha256
`{manifest["data"]["raw_sha256"][:16]}…`. Reproduction: `docs/REPRODUCIBILITY.md`. {manifest["measured_vs_illustrative"]}
"""
    )
    low = text.lower()
    hits = [p for p in OVERCLAIMS if p in low]
    if hits:
        raise ModelCardError(f"model card contains an unqualified over-claim: {hits}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text)
    return text


def load_inputs(cfg) -> dict[str, Any]:
    root = cfg.root
    tables = cfg.path_for("reports_dir") / "tables"
    manifest = json.loads((cfg.path_for("models_dir") / "manifest.json").read_text())
    fairness_path = cfg.path_for("reports_dir") / "fairness" / "group_metrics.json"
    method_path = cfg.path_for("reports_dir") / "explainability" / "method.json"
    lim_path = cfg.path_for("reports_dir") / "limitations.md"
    return {
        "manifest": manifest,
        "test_metrics": pd.read_csv(tables / "test_metrics.csv"),
        "test_k": pd.read_csv(tables / "test_recall_precision_at_k.csv"),
        "fairness": json.loads(fairness_path.read_text()) if fairness_path.is_file() else None,
        "explain_method": json.loads(method_path.read_text()) if method_path.is_file() else None,
        "limitations_md": lim_path.read_text()
        if lim_path.is_file()
        else "_reports/limitations.md not written yet._",
        "out_path": root / "reports" / "model_card.md",
    }
