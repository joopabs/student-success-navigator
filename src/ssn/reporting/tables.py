"""Render the data dictionary and the data overview from computed profile outputs.

Both renderers preserve a hand-written notes block delimited by
`<!-- BEGIN NOTES -->` / `<!-- END NOTES -->` across regenerations.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ssn.config import Config
from ssn.data.profile import ProfileOutputs
from ssn.data.schema import ValidationReport
from ssn.features.allowlist import Allowlist

NOTES_START, NOTES_END = "<!-- BEGIN NOTES -->", "<!-- END NOTES -->"
DEFAULT_NOTES = (
    f"{NOTES_START}\n_Add hand-written notes here; this block survives regeneration._\n{NOTES_END}"
)


def _existing_notes(path: Path) -> str:
    if path.is_file():
        m = re.search(
            re.escape(NOTES_START) + r".*?" + re.escape(NOTES_END), path.read_text(), re.S
        )
        if m:
            return m.group(0)
    return DEFAULT_NOTES


def _fmt(v: Any) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, float):
        return f"{v:.4g}" if abs(v) < 1e6 else f"{v:.3e}"
    return str(v)


def _md_table(df: pd.DataFrame, cols: list[str] | None = None) -> str:
    cols = cols or list(df.columns)
    head = "| " + " | ".join(cols) + " |\n|" + "|".join("---" for _ in cols) + "|\n"
    body = "\n".join(
        "| " + " | ".join(_fmt(r[c]).replace("|", "\\|") for c in cols) + " |"
        for _, r in df.iterrows()
    )
    return head + body + "\n"


def _codes_cell(meta: dict[str, Any], max_items: int = 6) -> str:
    codes = meta.get("codes") or {}
    if codes:
        items = [f"{k}={v}" for k, v in list(codes.items())[:max_items]]
        more = f" … (+{len(codes) - max_items} more)" if len(codes) > max_items else ""
        return "; ".join(items) + more
    if meta.get("range"):
        lo, hi = meta["range"]
        return f"[{lo}, {hi}]"
    return meta.get("units") or ""


def render_data_dictionary(
    cfg: Config, allow: Allowlist, prof: ProfileOutputs, report: ValidationReport, out_path: Path
) -> str:
    stats = prof.columns.set_index("column")
    checks = {c.name: c for c in report.column_checks}
    rows = []
    for name, meta in allow.columns.items():
        st = stats.loc[name] if name in stats.index else None
        chk = checks.get(name)
        observed = (
            ""
            if st is None
            else (
                f"{_fmt(st['min'])} – {_fmt(st['max'])}"
                if meta.get("dtype") == "numeric" and st["min"] is not None
                else f"{int(st['n_unique'])} distinct codes"
            )
        )
        verified = (
            "yes" if meta.get("encoding_verified") else ("n/a" if not meta.get("codes") else "NO")
        )
        if chk and chk.encoding_check == "mismatch":
            verified = f"NO (observed outside docs: {chk.observed_outside_codes})"
        rows.append(
            {
                "Column": name,
                "UCI name": meta.get("uci_name", name)
                if meta.get("uci_name", name) != name
                else "",
                "Availability": meta["availability"],
                "Role": meta["role"],
                "Type": meta["dtype"],
                "Documented values / range": _codes_cell(meta),
                "Observed": observed,
                "Missing": "" if st is None else int(st["n_missing"]),
                "Encoding verified": verified,
                "Description": (meta.get("description") or "").replace("\n", " "),
            }
        )
    dict_df = pd.DataFrame(rows)

    eng_rows = [
        {
            "Feature": n,
            "Inputs": ", ".join(e["inputs"]),
            "Adviser visible": e["adviser_visible"],
            "Audit only": e.get("audit_only", False),
            "Rationale": e.get("rationale", ""),
        }
        for n, e in allow.engineered.items()
    ]
    eng_md = _md_table(pd.DataFrame(eng_rows)) if eng_rows else "_None yet (Milestone 3)._\n"

    code_tables = []
    for name, meta in allow.columns.items():
        if meta.get("codes"):
            cv = prof.categorical_values[prof.categorical_values["column"] == name]
            counts = dict(zip(cv["code"], cv["count"], strict=False))
            tbl = pd.DataFrame(
                [
                    {"Code": k, "Label": v, "Observed count": counts.get(int(k), 0)}
                    for k, v in meta["codes"].items()
                ]
            )
            undocumented = cv[cv["documented"] == False]  # noqa: E712
            extra = (
                ""
                if undocumented.empty
                else (
                    "\n**Observed codes not in documentation:** "
                    + ", ".join(
                        f"{int(r.code)} (n={int(r['count'])})" for _, r in undocumented.iterrows()
                    )
                    + "\n"
                )
            )
            code_tables.append(
                f"### {name}\n\nSource: {meta.get('encoding_source', 'unverified')}\n\n{_md_table(tbl)}{extra}"
            )

    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    text = f"""# Data Dictionary

**Dataset:** UCI 697, Predict Students' Dropout and Academic Success. **Generated:** {generated} by
`python -m ssn data profile`. Do not edit the generated tables; hand-written notes go in the notes block.

**Unit of analysis:** one student enrollment record (UCI: "Each instance is a student").
**Rows × columns observed:** {report.n_rows} × {report.n_cols}.

Availability classes: `enrollment` (known at enrollment), `first_semester` (end of semester 1),
`second_semester` (prohibited for the deployed model), `outcome` (the target), `ambiguous`
(timing undocumented; excluded by default, see research R-05). Roles: `feature`, `sensitive`
(aggregate fairness auditing only, never a model input), `target`.

## Columns

{_md_table(dict_df)}
## Engineered features

{eng_md}
## Encoding verification

Codes come from the UCI variables table (API `https://archive.ics.uci.edu/api/dataset?id=697`,
retrieved 2026-09-10; see data/README.md).
"Encoding verified: yes" means every observed code appears in the documentation. Observed counts are
computed from the data.

{"".join(code_tables)}
{_existing_notes(out_path)}
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text)
    return text


def render_data_overview(
    cfg: Config,
    allow: Allowlist,
    prof: ProfileOutputs,
    report: ValidationReport,
    out_path: Path,
    raw_sha256: str,
) -> str:
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    tgt = prof.target
    pos_rate = tgt.attrs.get("is_dropout_positive_rate")
    cc = report.classification_counts
    types = prof.columns.groupby("dtype")["column"].count().to_dict()
    avail = prof.columns.groupby("availability")["column"].count().to_dict()
    missing_total = int(prof.columns["n_missing"].sum())
    inv = prof.invalid_values
    inv_nonzero = inv[inv["count"] > 0]
    unverified = [
        n for n, m in allow.columns.items() if m.get("codes") and not m.get("encoding_verified")
    ]
    mismatched = [c.name for c in report.column_checks if c.encoding_check == "mismatch"]
    dup = prof.duplicates
    missing_md = (
        _md_table(
            prof.columns[prof.columns["n_missing"] > 0][["column", "n_missing", "pct_missing"]]
        )
        if missing_total
        else "_No missing values observed in any column._\n"
    )
    invalid_md = (
        _md_table(inv_nonzero)
        if not inv_nonzero.empty
        else "_No values violate the documented codes or ranges._\n"
    )

    text = f"""# Data Overview

**Generated:** {generated} by `python -m ssn data profile`. Every number below is computed from
`data/raw/data.csv` (sha256 `{raw_sha256}`). Hand-written commentary lives in the notes block.

## 1. Source and citation

- **Dataset:** Predict Students' Dropout and Academic Success (UCI ML Repository id 697)
- **URL:** https://archive.ics.uci.edu/dataset/697/predict+students+dropout+and+academic+success
- **DOI:** 10.24432/C5MC89 · **Licence:** CC BY 4.0
- **Creators:** Valentim Realinho, Mónica Vieira Martins, Jorge Machado, Luís Baptista
  (Instituto Politécnico de Portalegre)
- **Citation (UCI recommended):** Realinho, V., Vieira Martins, M., Machado, J., & Baptista, L. (2021).
  Predict Students' Dropout and Academic Success [Dataset]. UCI Machine Learning Repository.
  https://doi.org/10.24432/C5MC89
- **Introductory paper (UCI "citation" field):** Martins, M.V., Tolledo, D., Machado, J., Baptista, L.M.T.,
  Realinho, V. (2021). Early prediction of student's performance in higher education: a case study.
  *Trends and Applications in Information Systems and Technologies*, AISC, Springer.
  DOI 10.1007/978-3-030-72657-7_16
- **Funding (UCI):** SATDAP – Capacitação da Administração Pública, grant POCI-05-5762-FSE-000191, Portugal.

## 2. Access and licence verification checklist

See `data/README.md` for the dated checklist. Items: licence text read; attribution present in
README, report, and decks; raw file Git-ignored; checksum recorded; source spelling preserved.

## 3. Unit of analysis and target

- **Unit of analysis:** one student enrollment record ("Each instance is a student").
- **Source target:** `{cfg.get("data.target_column")}`, three classes "at the end of the normal duration
  of the course" (UCI). **Deployed target:** `is_dropout` = 1 where Target = {cfg.get("data.target_positive_label")},
  else 0 (PROJECT_DECISIONS).

### Target distribution (observed)

{_md_table(tgt, ["label", "count", "share", "is_dropout"])}
Derived `is_dropout` positive rate: **{pos_rate}**.

## 4. Shape and column classification (observed)

- Rows: **{report.n_rows}** · Columns: **{report.n_cols}** (36 features + Target per UCI; verified against the file)
- Availability classes: {avail}
- Roles: allowed model inputs = {cc["allowed"]}, sensitive (audit-only) = {cc["sensitive"]},
  ambiguous (excluded by default) = {cc["ambiguous"]}, second semester (prohibited) = {cc["second_semester"]},
  target = {cc["target"]}, unclassified = {cc["unclassified"]}
- Declared types: {types}

## 5. Missingness

Total missing cells across all columns: **{missing_total}** (UCI declares "has_missing_values: no").

{missing_md}
## 6. Duplicates

{_md_table(dup)}
## 7. Invalid values against documentation

Rules: non-numeric/missing, code not in UCI documentation, outside documented range, negative counts.

{invalid_md}
Columns with documented codes but **unverified** encoding: {unverified or "none"}.
Columns whose observed codes fall **outside** documentation: {mismatched or "none"}.

## 8. Outlier candidates (IQR fences, numeric columns)

Counts only; treatment decisions belong to Milestone 3 and must be justified there.

{_md_table(prof.outliers)}
## 9. Dataset limitations (documented, not inferred from results)

- Single institution in Portugal; not representative of Philippine or other institutions.
- Historic outcomes may encode institutional inequities; predicted risk is not causal.
- "Enrolled" students had not yet graduated or left at the observation horizon; the binary target
  treats them as non-dropout by project decision.
- Financial-status fields (Debtor, Tuition fees up to date, Scholarship holder) have no documented
  recording time and are classified `ambiguous` and excluded by default (leakage guard).
- Macroeconomic indicators are annual national figures, not student-level attributes.
- UCI states preprocessing removed anomalies, outliers, and missing values before publication;
  the cleaning history is therefore not fully observable.
- The documentation entry for "Curricular units 2nd sem (without evaluations)" says "1st semester";
  treated as a documentation typo.

{_existing_notes(out_path)}
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text)
    return text
