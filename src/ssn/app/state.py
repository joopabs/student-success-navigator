"""Application state loaded ONCE at startup from persisted artifacts and reports.

The app never fits anything and never opens the processed or evaluator-only data directories. It
serves no scores when the artifact fails verification (version or checksum): a blocked state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from ssn.app.services.action_log import ActionLog
from ssn.app.services.equity import load_equity
from ssn.app.services.explanations import PrecomputedShap
from ssn.app.services.inference import (
    ArtifactBundle,
    ArtifactError,
    load_bundle,
    load_reference_medians,
    score_frame,
)
from ssn.app.services.prioritization import k_options, rank_cohort
from ssn.app.services.validation import FieldSpec, build_fields
from ssn.config import Config
from ssn.explain import language as L

RECORD_ID = "record_id"


@dataclass
class AppState:
    cfg: Config
    bundle: ArtifactBundle | None
    cohort: pd.DataFrame
    ranked: pd.DataFrame
    shap: PrecomputedShap | None
    rules: L.LanguageRules
    reference: dict[str, float]
    fields: list[FieldSpec]
    equity: dict[str, Any] | None
    model_card_md: str
    limitations_md: str
    test_k: pd.DataFrame | None
    action_log: ActionLog
    k_default: int
    k_options: list[int]
    per_week: int
    window_weeks: int
    disclaimer: str
    non_use: str
    blocked_reason: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def blocked(self) -> bool:
        return self.blocked_reason is not None

    def record(self, record_id: str) -> pd.Series | None:
        m = self.cohort[self.cohort[RECORD_ID] == record_id]
        return None if m.empty else m.iloc[0]

    def ranked_row(self, record_id: str) -> pd.Series | None:
        m = self.ranked[self.ranked[RECORD_ID] == record_id]
        return None if m.empty else m.iloc[0]


DISCLAIMER = (
    "Illustrative decision support for a capstone demonstration. Scores are not causal, not a "
    "judgement of any student, and not production-ready. Every suggestion is advisory: a qualified "
    "adviser reviews each record and decides. No automated or adverse decision is made or "
    "recommended."
)


def _read(p: Path, fallback: str) -> str:
    return p.read_text() if p.is_file() else fallback


def _common(cfg: Config) -> dict[str, Any]:
    rules = L.load(cfg.path_for("language_yaml"))
    reports = cfg.path_for("reports_dir")
    tk = reports / "tables" / "test_recall_precision_at_k.csv"
    return {
        "rules": rules,
        "reference": load_reference_medians(cfg),
        "equity": load_equity(cfg),
        "model_card_md": _read(
            reports / "model_card.md",
            "_Model card not generated yet (run `python -m ssn model-card`)._",
        ),
        "limitations_md": _read(reports / "limitations.md", "_Limitations not written yet._"),
        "test_k": pd.read_csv(tk) if tk.is_file() else None,
        "action_log": ActionLog(cfg.path_for("app.actions_db")),
        "k_default": int(cfg.get("capacity.k")),
        "k_options": k_options(cfg),
        "per_week": int(cfg.get("capacity.per_week")),
        "window_weeks": int(cfg.get("capacity.window_weeks")),
        "disclaimer": DISCLAIMER,
    }


def blocked_state(cfg: Config, reason: str) -> AppState:
    c = _common(cfg)
    return AppState(
        cfg=cfg,
        bundle=None,
        cohort=pd.DataFrame(columns=[RECORD_ID]),
        ranked=pd.DataFrame(),
        shap=None,
        fields=[],
        non_use="",
        blocked_reason=reason,
        **c,
    )


def load_state(cfg: Config) -> AppState:
    try:
        bundle = load_bundle(cfg)
    except ArtifactError as exc:
        return blocked_state(cfg, f"Model artifact failed verification: {exc}")
    demo_path = cfg.path_for("demo_dir") / "demo_cohort.parquet"
    if not demo_path.is_file():
        return blocked_state(
            cfg, f"Demo cohort not found at {demo_path}. Run `python -m ssn data split`."
        )
    cohort = pd.read_parquet(demo_path)
    forbidden = {"Target", "is_dropout", "age_band"} | set(bundle.allow.sensitive)
    leaked = sorted(forbidden & set(cohort.columns))
    if leaked:
        return blocked_state(
            cfg, f"Demo cohort contains adviser-forbidden columns {leaked}; refusing to serve."
        )
    scores = score_frame(bundle, cohort)  # predict_proba only
    ranked = rank_cohort(cohort[RECORD_ID], scores, bundle.bands)
    shap_path = cfg.path_for("reports_dir") / "explainability" / "shap_values_test.npz"
    shap = PrecomputedShap.load(shap_path) if shap_path.is_file() else None
    c = _common(cfg)
    fields = build_fields(bundle.schema, bundle.allow, c["rules"])
    return AppState(
        cfg=cfg,
        bundle=bundle,
        cohort=cohort,
        ranked=ranked,
        shap=shap,
        fields=fields,
        non_use=str(bundle.manifest.get("non_use", "")),
        **c,
    )
