from __future__ import annotations

import ast
from pathlib import Path

APP = Path("src/ssn/app")
FORBIDDEN_MODULES = {
    "ssn.modeling.evaluate",
    "ssn.modeling.evaluate_test",
    "ssn.modeling.tune",
    "ssn.modeling.traincv",
    "ssn.modeling.select_model",
    "ssn.fairness.audit",
    "ssn.fairness.mitigate",
    "ssn.data.split",
    "ssn.data.clean",
}
FORBIDDEN_STRINGS = (
    "data/evaluation",
    "data/processed",
    "demo_cohort_labels",
    "test.parquet",
    "train.parquet",
)


def _py_files():
    return sorted(p for p in APP.rglob("*.py"))


def test_app_never_calls_fit():
    for p in _py_files():
        tree = ast.parse(p.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "fit",
                    "fit_transform",
                    "fit_resample",
                    "partial_fit",
                }, f"{p}: {node.func.attr}"


def test_app_never_imports_training_or_label_modules():
    for p in _py_files():
        tree = ast.parse(p.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for n in names:
                assert n not in FORBIDDEN_MODULES, f"{p} imports {n}"


def test_app_never_references_evaluation_or_processed_paths():
    for p in _py_files():
        text = p.read_text()
        for s in FORBIDDEN_STRINGS:
            assert s not in text, f"{p} mentions {s}"
