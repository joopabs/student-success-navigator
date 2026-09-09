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


def scan_text(text: str, rules: LanguageRules, path: str = "<text>") -> list[Finding]:
    findings: list[Finding] = []
    for i, line in enumerate(text.splitlines(), start=1):
        low = line.lower()
        for term in rules.prohibited_terms:
            if term in low:
                findings.append(Finding("prohibited-term", path, i, line))
        for phrase in rules.overclaim_phrases:
            if phrase in low:
                findings.append(Finding("fairness-overclaim", path, i, line))
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
        findings.extend(scan_text(text, rules, path=str(f)))
    return findings


def missing_feature_entries(rules: LanguageRules, feature_names: list[str]) -> list[str]:
    """Allow-listed or engineered features without a language entry (enforced from T060)."""
    return [f for f in feature_names if f not in rules.features]
