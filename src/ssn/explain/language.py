"""Adviser-facing language rules: prohibited terms, unlabeled business figures, over-claims.

Contract: research R-18; constitution Principles II and XI.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SCAN_EXTENSIONS = {".py", ".md", ".yaml", ".yml", ".ipynb", ".txt", ".html"}
FIGURE_RE = re.compile(r"(?:[$€£₱]\s?\d[\d,]*(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?\s?%)")


@dataclass(frozen=True)
class Finding:
    rule: str
    path: str
    line: int
    snippet: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: [{self.rule}] {self.snippet.strip()[:120]}"


@dataclass(frozen=True)
class LanguageRules:
    prohibited_terms: tuple[str, ...]
    business_terms: tuple[str, ...]
    assumption_labels: tuple[str, ...]
    overclaim_phrases: tuple[str, ...]
    features: dict[str, dict[str, Any]]
    source: Path | None = None


def load(path: str | Path = "configs/language.yaml") -> LanguageRules:
    raw = yaml.safe_load(Path(path).read_text()) or {}
    return LanguageRules(
        prohibited_terms=tuple(t.lower() for t in raw.get("prohibited_terms", [])),
        business_terms=tuple(t.lower() for t in raw.get("business_terms", [])),
        assumption_labels=tuple(t.lower() for t in raw.get("assumption_labels", [])),
        overclaim_phrases=tuple(t.lower() for t in raw.get("overclaim_phrases", [])),
        features=dict(raw.get("features") or {}),
        source=Path(path).resolve(),
    )


def _paragraphs(text: str) -> list[tuple[int, str]]:
    """Split text into (starting line number, paragraph) pairs."""
    out: list[tuple[int, str]] = []
    start, buf = 1, []
    for i, line in enumerate(text.splitlines(), start=1):
        if line.strip():
            if not buf:
                start = i
            buf.append(line)
        elif buf:
            out.append((start, "\n".join(buf)))
            buf = []
    if buf:
        out.append((start, "\n".join(buf)))
    return out


PROSE_EXTENSIONS = {".md", ".ipynb", ".txt", ".html", "<text>"}


def scan_text(
    text: str, rules: LanguageRules, path: str = "<text>", *, business_rule: bool = True
) -> list[Finding]:
    findings: list[Finding] = []
    for i, line in enumerate(text.splitlines(), start=1):
        low = line.lower()
        for term in rules.prohibited_terms:
            if term in low:
                findings.append(Finding("prohibited-term", path, i, line))
        for phrase in rules.overclaim_phrases:
            if phrase in low:
                findings.append(Finding("fairness-overclaim", path, i, line))
    if not business_rule:
        return findings
    for start, para in _paragraphs(text):
        low = para.lower()
        has_business = any(re.search(rf"\b{re.escape(t)}\b", low) for t in rules.business_terms)
        has_figure = FIGURE_RE.search(para) is not None
        labelled = any(lbl in low for lbl in rules.assumption_labels)
        if has_business and has_figure and not labelled:
            findings.append(Finding("unlabeled-business-figure", path, start, para.splitlines()[0]))
    return findings


def _notebook_text(path: Path) -> str:
    try:
        nb = json.loads(path.read_text())
    except json.JSONDecodeError:
        return path.read_text(errors="ignore")
    chunks = []
    for cell in nb.get("cells", []):
        src = cell.get("source", [])
        chunks.append("".join(src) if isinstance(src, list) else str(src))
    return "\n\n".join(chunks)


def iter_files(paths: list[str | Path], extensions: set[str] = SCAN_EXTENSIONS) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files.extend(
                f
                for f in sorted(p.rglob("*"))
                if f.is_file() and f.suffix in extensions and ".ipynb_checkpoints" not in f.parts
            )
        elif p.is_file():
            files.append(p)
    return files


def scan_paths(paths: list[str | Path], rules: LanguageRules) -> list[Finding]:
    findings: list[Finding] = []
    for f in iter_files(paths):
        if rules.source is not None and f.resolve() == rules.source:
            continue  # the rules file necessarily contains the phrases it forbids
        text = _notebook_text(f) if f.suffix == ".ipynb" else f.read_text(errors="ignore")
        # business-figure rule targets prose; code and config carry `value`/`100%` legitimately
        findings.extend(
            scan_text(text, rules, path=str(f), business_rule=f.suffix in PROSE_EXTENSIONS)
        )
    return findings


def missing_feature_entries(rules: LanguageRules, feature_names: list[str]) -> list[str]:
    """Allow-listed or engineered features without a language entry (enforced from T060)."""
    return [f for f in feature_names if f not in rules.features]


PROHIBITED_REASON_FEATURES_MSG = "sensitive attribute cannot be shown as an adviser-facing reason"


def _situation_phrase(
    meta: dict[str, Any], value: Any, shap_value: float, reference: dict[str, float] | None
) -> str:
    """Pick the phrase that describes the record's situation.

    numeric: value above the training median -> higher_phrase, else lower_phrase (needs
    `reference`);
    binary: value >= 0.5 -> higher_phrase else lower_phrase;
    categorical codes have no order: a positive contribution -> higher_phrase (written as
    "associated with higher support needs in past cohorts"), otherwise lower_phrase.
    """
    kind = meta.get("value_kind", "numeric")
    if isinstance(value, float) and value != value:  # NaN (e.g. undefined rate) -> unknown
        value = None
    if kind == "binary" and value is not None:
        return meta["higher_phrase"] if float(value) >= 0.5 else meta["lower_phrase"]
    if kind == "numeric" and value is not None and reference and meta_name(meta) in reference:
        return (
            meta["higher_phrase"]
            if float(value) > reference[meta_name(meta)]
            else meta["lower_phrase"]
        )
    return meta["higher_phrase"] if shap_value > 0 else meta["lower_phrase"]


def meta_name(meta: dict[str, Any]) -> str:
    return meta.get("_name", "")


def render_local(
    contributions: list[dict[str, Any]],
    rules: LanguageRules,
    top: int = 5,
    reference: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Turn (feature, shap, value) contributions into supportive adviser phrases.

    Features with `adviser_visible: false` (sensitive attributes) are dropped, never rendered.
    `phrase` describes the record's situation; `direction` gives the sign of the contribution
    (positive SHAP raises the support-priority score). `reference` maps numeric feature -> training
    median, used to decide whether a value counts as higher or lower than typical.
    """
    out: list[dict[str, Any]] = []
    for c in contributions:
        meta = rules.features.get(c["feature"])
        if meta is None or not meta.get("adviser_visible", False):
            continue
        meta = {**meta, "_name": c["feature"]}
        shap_value = float(c["shap"])
        out.append(
            {
                "label": meta["label"],
                "phrase": _situation_phrase(meta, c.get("value"), shap_value, reference),
                "direction": "raises support priority"
                if shap_value > 0
                else "lowers support priority",
                "strength": abs(shap_value),
            }
        )
        if len(out) >= top:
            break
    return out


def missing_language_entries(rules: LanguageRules, allow) -> list[str]:
    """Allow-listed source + engineered features without a language entry (T060 completeness)."""
    names = sorted(allow.allowed_source) + list(allow.engineered)
    return [n for n in names if n not in rules.features]
