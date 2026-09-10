from __future__ import annotations

from pathlib import Path

REQUIRED_EXCLUDES = [
    "data/raw",
    "data/processed",
    "data/evaluation",
    "data/local",
    ".env",
    "references",
    ".venv",
    ".git",
    "models/candidates",
]


def test_dockerignore_excludes_private_and_evaluator_data():
    text = Path(".dockerignore").read_text().splitlines()
    rules = {line.strip() for line in text if line.strip() and not line.startswith("#")}
    for pattern in REQUIRED_EXCLUDES:
        assert pattern in rules, f".dockerignore must exclude {pattern}"


def test_dockerfile_copies_only_runtime_inputs():
    text = Path("Dockerfile").read_text()
    for allowed in ("COPY src", "COPY configs", "COPY models", "COPY data/demo", "COPY reports"):
        assert allowed in text
    for forbidden in (
        "COPY data ",
        "COPY data/raw",
        "COPY data/processed",
        "COPY data/evaluation",
        "COPY tests",
        "COPY notebooks",
        "COPY .",
    ):
        assert forbidden not in text, forbidden
    assert "fit(" not in text and "train" not in text.lower().replace("training split", "")
