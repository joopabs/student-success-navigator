"""Fit the final pipeline on the full training split and persist it with a manifest (T053).

Contract: specs/001-dropout-risk-navigator/contracts/artifact-manifest.md. The manifest carries
provenance (git sha, config hash, library versions, seed), the exact input schema the pipeline
expects, the threshold and bands, CV summary, and placeholders for the single test evaluation.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

import ssn
from ssn.config import Config, load_model_config
from ssn.features.allowlist import Allowlist
from ssn.features.engineering import ENGINEERED_NAMES
from ssn.features.preprocess import project_for_model
from ssn.modeling.calibrate import wrap_calibrated
from ssn.modeling.candidates import SelectionSetting, build_pipeline

IS_DROPOUT = "is_dropout"
PIPELINE_FILE = "final_pipeline.joblib"
MANIFEST_FILE = "manifest.json"
DISCLAIMER = (
    "Scores are illustrative decision support for voluntary, supportive adviser outreach. "
    "They are not causal, not a judgement of a student, and not production-ready without "
    "institutional validation. All outreach decisions require qualified human review."
)
NON_USE = (
    "No automated or adverse decisions about admission, enrollment, scholarships, financial "
    "aid, grades, discipline, housing, or student opportunities."
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _relative_or_models(path: Path, root: Path) -> str:
    """Repo-relative path when possible; otherwise `models/<name>` (e.g. temp dirs in tests)."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(Path("models") / path.name)


def _git_sha(root: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:  # noqa: BLE001 - git may be unavailable
        return None


def library_versions() -> dict[str, str]:
    import imblearn
    import numpy
    import shap
    import sklearn

    return {
        "scikit-learn": sklearn.__version__,
        "numpy": numpy.__version__,
        "pandas": pd.__version__,
        "shap": shap.__version__,
        "imbalanced-learn": imblearn.__version__,
        "joblib": joblib.__version__,
        "ssn": ssn.__version__,
    }


def input_schema(
    allow: Allowlist, ranges: dict[str, dict[str, float]] | None
) -> list[dict[str, Any]]:
    """Exact columns the pipeline expects, with documented codes or observed ranges."""
    schema = []
    for name in sorted(allow.allowed_source):
        meta = allow.columns[name]
        entry: dict[str, Any] = {
            "name": name,
            "dtype": meta["dtype"],
            "availability": meta["availability"],
        }
        if meta.get("codes"):
            entry["allowed_codes"] = [int(k) for k in meta["codes"]]
        elif meta.get("range"):
            entry["documented_range"] = list(meta["range"])
        if ranges and name in ranges:
            entry["observed_range_raw"] = ranges[name]
        schema.append(entry)
    return schema


def build_final_pipeline(
    cfg: Config,
    allow: Allowlist,
    decision: dict[str, Any],
    calibration: dict[str, Any],
    selection: SelectionSetting | None,
):
    sel = selection if decision["selection"] == "decided" else None
    pipe = build_pipeline(
        decision["model"], cfg, allow, selection=sel, params_override=decision["best_params"]
    )
    if calibration.get("applied"):
        return wrap_calibrated(pipe, calibration["method"], cv=int(calibration.get("inner_cv", 5)))
    return pipe


def build_manifest(
    cfg: Config,
    allow: Allowlist,
    decision: dict[str, Any],
    calibration: dict[str, Any],
    threshold: dict[str, Any],
    matrix_row: dict[str, Any],
    pipeline_path: Path,
    n_train: int,
    positive_rate_train: float,
    n_test: int | None,
    positive_rate_test: float | None,
    raw_sha256: str,
    selection: SelectionSetting | None,
    model_cfg_path: Path,
    ranges: dict[str, dict[str, float]] | None,
    selected_features: list[str] | None,
) -> dict[str, Any]:
    mc = load_model_config(decision["model"], cfg)
    cfg_hash = hashlib.sha256(cfg.path.read_bytes() + model_cfg_path.read_bytes()).hexdigest()
    return {
        "model_version": cfg.get("project.model_version"),
        "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_sha": _git_sha(cfg.root),
        "config_sha256": cfg_hash,
        "pipeline_file": _relative_or_models(pipeline_path, cfg.root),
        "pipeline_sha256": sha256_file(pipeline_path),
        "python_version": platform.python_version(),
        "library_versions": library_versions(),
        "seed": cfg.seed,
        "data": {
            "source": "UCI ML Repository dataset 697",
            "doi": "10.24432/C5MC89",
            "license": "CC BY 4.0",
            "raw_sha256": raw_sha256,
            "n_train": int(n_train),
            "n_test": n_test,
            "positive_rate_train": round(float(positive_rate_train), 4),
            "positive_rate_test": None
            if positive_rate_test is None
            else round(float(positive_rate_test), 4),
        },
        "target": {
            "name": IS_DROPOUT,
            "positive_label": cfg.get("data.target_positive_label"),
            "negative_labels": [
                lbl
                for lbl in cfg.get("data.target_expected_labels")
                if lbl != cfg.get("data.target_positive_label")
            ],
        },
        "features": {
            "allowlisted_source": sorted(allow.allowed_source),
            "engineered": list(ENGINEERED_NAMES),
            "prohibited_excluded": sorted(
                c
                for c in allow.prohibited
                if allow.columns.get(c, {}).get("availability") == "second_semester"
            ),
            "ambiguous_excluded": sorted(allow.ambiguous),
            "sensitive_excluded_audit_only": sorted(allow.sensitive),
            "selection_setting": None
            if decision["selection"] != "decided" or selection is None
            else selection.__dict__,
            "selected_after_selection": selected_features,
            "input_schema": input_schema(allow, ranges),
        },
        "estimator": {
            "name": decision["model"],
            "class": mc.estimator,
            "params": {**mc.params, **decision["best_params"]},
        },
        "calibration": {
            "applied": bool(calibration.get("applied")),
            "method": calibration.get("method"),
        },
        "imbalance_treatment": (
            "class_weight (SMOTENC rejected under research R-07; "
            "see reports/model_comparison_cv.md)"
        ),
        "threshold": {
            "rule": threshold["rule"],
            "capacity_per_week": threshold["capacity_per_week"],
            "window_weeks": threshold["window_weeks"],
            "capacity_k": threshold["capacity_k"],
            "capacity_illustrative": True,
            "n_cohort_expected": threshold["n_cohort_expected"],
            "value": threshold["threshold"],
            "selection_rate_oof": threshold["selection_rate"],
        },
        "bands": threshold["bands"],
        "selection_rationale": decision["rationale"] + " Rule: " + decision["rule"],
        "cv_summary": {
            k: matrix_row[k]
            for k in [
                "pr_auc",
                "pr_auc_std_cv",
                "roc_auc",
                "recall_at_k",
                "precision_at_k",
                "brier",
                "ece",
                "fairness_max_dp_difference",
                "fairness_min_di_ratio",
            ]
        },
        "test_evaluations": 0,
        "test_summary": {
            "pr_auc": None,
            "roc_auc": None,
            "recall_at_k": None,
            "precision_at_k": None,
            "brier": None,
            "ece": None,
        },
        "zero_predicted_positives_on_test": None,
        "fairness_summary_file": "reports/fairness/group_metrics.json",
        "explainability_files": [],
        "intended_use": (
            "Decision support for voluntary, supportive adviser outreach after the first semester."
        ),
        "non_use": NON_USE,
        "disclaimer": DISCLAIMER,
        "measured_vs_illustrative": (
            "cv_summary and test_summary are MEASURED on data; capacity_k, window_weeks and any "
            "share-of-dropouts-reached figure are ILLUSTRATIVE assumptions."
        ),
    }


def selected_feature_names(pipeline) -> list[str] | None:
    """Transformed feature names surviving the selector, if the pipeline has one."""
    try:
        inner = (
            pipeline.calibrated_classifiers_[0].estimator
            if hasattr(pipeline, "calibrated_classifiers_")
            else pipeline
        )
        names = inner.named_steps["pre"].get_feature_names_out()
        if "select" in inner.named_steps:
            mask = inner.named_steps["select"].get_support()
            return [str(n) for n, m in zip(names, mask, strict=False) if m]
        return [str(n) for n in names]
    except Exception:  # noqa: BLE001
        return None


def fit_and_persist(
    train: pd.DataFrame,
    cfg: Config,
    allow: Allowlist,
    decision: dict[str, Any],
    calibration: dict[str, Any],
    threshold: dict[str, Any],
    matrix_row: dict[str, Any],
    selection: SelectionSetting | None,
    models_dir: Path,
    raw_sha256: str,
    ranges: dict[str, dict[str, float]] | None,
    n_test: int | None = None,
    positive_rate_test: float | None = None,
) -> dict[str, Any]:
    X = project_for_model(train, allow)
    y = train[IS_DROPOUT].astype(int)
    pipe = build_final_pipeline(cfg, allow, decision, calibration, selection)
    pipe.fit(X, y)
    models_dir.mkdir(parents=True, exist_ok=True)
    pipeline_path = models_dir / PIPELINE_FILE
    joblib.dump(pipe, pipeline_path)
    model_cfg_path = cfg.root / "configs" / "models" / f"{decision['model']}.yaml"
    manifest = build_manifest(
        cfg,
        allow,
        decision,
        calibration,
        threshold,
        matrix_row,
        pipeline_path,
        len(X),
        float(y.mean()),
        n_test,
        positive_rate_test,
        raw_sha256,
        selection,
        model_cfg_path,
        ranges,
        selected_feature_names(pipe),
    )
    (models_dir / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    return manifest


class ArtifactError(RuntimeError):
    pass


def load_artifact(models_dir: Path, expected_version: str | None = None):
    """Load manifest + pipeline, verifying version and checksum. Returns (manifest, pipeline)."""
    manifest_path = models_dir / MANIFEST_FILE
    if not manifest_path.is_file():
        raise ArtifactError(f"manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text())
    if expected_version is not None and manifest["model_version"] != expected_version:
        raise ArtifactError(
            f"model_version {manifest['model_version']!r} != expected {expected_version!r}"
        )
    pipeline_path = models_dir / Path(manifest["pipeline_file"]).name
    if not pipeline_path.is_file():
        raise ArtifactError(
            f"pipeline file not found: {pipeline_path}; run `python -m ssn fit-final`"
        )
    actual = sha256_file(pipeline_path)
    if actual != manifest["pipeline_sha256"]:
        raise ArtifactError(
            f"pipeline sha256 mismatch: manifest {manifest['pipeline_sha256'][:12]}..., "
            f"file {actual[:12]}..."
        )
    return manifest, joblib.load(pipeline_path)


def validate_input_frame(X: pd.DataFrame, manifest: dict[str, Any]) -> list[str]:
    """Return a list of schema problems (empty if X matches the manifest input schema)."""
    problems = []
    expected = [c["name"] for c in manifest["features"]["input_schema"]]
    missing = [c for c in expected if c not in X.columns]
    extra = [c for c in X.columns if c not in expected]
    if missing:
        problems.append(f"missing columns: {missing}")
    if extra:
        problems.append(f"unexpected columns: {extra}")
    for c in manifest["features"]["input_schema"]:
        if c["name"] in X.columns and "allowed_codes" in c:
            bad = set(pd.to_numeric(X[c["name"]], errors="coerce").dropna().astype(int)) - set(
                c["allowed_codes"]
            )
            if bad:
                problems.append(f"{c['name']}: codes not in schema {sorted(bad)}")
    return problems
