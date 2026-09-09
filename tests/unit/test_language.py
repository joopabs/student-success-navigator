from __future__ import annotations

import subprocess
import sys

from ssn.explain import language as L

RULES = L.load("configs/language.yaml")


def _rules(findings):
    return sorted({f.rule for f in findings})


def test_rules_loaded():
    assert "at risk of failing" in RULES.prohibited_terms
    assert "illustrative" in RULES.assumption_labels


def test_prohibited_term_flagged_case_insensitive():
    f = L.scan_text("This student is LIKELY TO DROP OUT next term.", RULES)
    assert _rules(f) == ["prohibited-term"]


def test_unlabeled_business_figure_flagged():
    text = "Projected ROI is 35% in year one.\n\nSeparate paragraph with nothing."
    assert _rules(L.scan_text(text, RULES)) == ["unlabeled-business-figure"]


def test_labeled_business_figure_passes():
    text = (
        "Illustrative ROI of 35% under stated assumptions; capacity of 10 per week is illustrative."
    )
    assert L.scan_text(text, RULES) == []


def test_business_term_without_figure_passes():
    assert L.scan_text("Outreach capacity is configurable.", RULES) == []


def test_overclaim_flagged():
    assert _rules(L.scan_text("Therefore the model is fair.", RULES)) == ["fairness-overclaim"]


def test_clean_text_passes():
    assert (
        L.scan_text("Support-priority scores help advisers plan voluntary outreach.", RULES) == []
    )


def test_readme_and_data_readme_are_clean():
    assert L.scan_paths(["README.md", "data/README.md"], RULES) == []


def test_notebook_cells_are_scanned(tmp_path):
    nb = {"cells": [{"cell_type": "markdown", "source": ["A problem student appears here."]}]}
    p = tmp_path / "x.ipynb"
    p.write_text(__import__("json").dumps(nb))
    assert _rules(L.scan_paths([p], RULES)) == ["prohibited-term"]


def test_cli_exits_one_on_findings(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_text("He is a failing student.\n")
    r = subprocess.run(
        [sys.executable, "-m", "ssn", "scan-language", "--paths", str(bad)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 1 and "prohibited-term" in r.stdout


def test_cli_exits_zero_on_clean_paths():
    r = subprocess.run(
        [sys.executable, "-m", "ssn", "scan-language", "--paths", "README.md"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_rules_file_itself_is_skipped():
    assert L.scan_paths(["configs"], RULES) == []
