# Contract: Model Artifact Manifest (`models/manifest.json`)

Written by `fit-final`, updated by `evaluate-test` (test evaluation counter and test metrics
summary only). Always committed. Read by the app at startup and by `model-card`.

```json
{
  "model_version": "1.0.0",
  "created_at": "2026-09-09T10:00:00Z",
  "git_sha": "<40-hex>",
  "config_sha256": "<sha256 of resolved base.yaml + model yaml>",
  "pipeline_file": "models/final_pipeline.joblib",
  "pipeline_sha256": "<sha256>",
  "python_version": "3.11.x",
  "library_versions": {"scikit-learn": "...", "numpy": "...", "pandas": "...", "shap": "..."},
  "seed": 42,
  "data": {
    "source": "UCI ML Repository dataset 697",
    "doi": "10.24432/C5MC89",
    "license": "CC BY 4.0",
    "raw_sha256": "<sha256>",
    "n_train": 0,
    "n_test": 0,
    "positive_rate_train": 0.0,
    "positive_rate_test": 0.0
  },
  "target": {"name": "is_dropout", "positive_label": "Dropout", "negative_labels": ["Enrolled", "Graduate"]},
  "features": {
    "allowlisted_source": ["..."],
    "engineered": ["..."],
    "prohibited_excluded": ["..."],
    "ambiguous_excluded": ["..."],
    "selected_after_selection": ["..."]
  },
  "estimator": {"name": "hist_gb", "class": "sklearn.ensemble.HistGradientBoostingClassifier", "params": {}},
  "calibration": {"applied": false, "method": null},
  "imbalance_treatment": "class_weight=balanced",
  "threshold": {
    "rule": "oof_quantile_for_capacity",
    "capacity_k": 50,
    "capacity_illustrative": true,
    "n_cohort_expected": 0,
    "value": 0.0
  },
  "bands": [
    {"name": "Priority outreach", "lower": 0.0, "upper": 1.0},
    {"name": "Check-in suggested", "lower": 0.0, "upper": 0.0},
    {"name": "Standard support", "lower": 0.0, "upper": 0.0}
  ],
  "selection_rationale": "See reports/tables/selection_matrix.csv; criteria: PR-AUC, Recall@K, Precision@K, Brier/ECE, fairness summary, explainability, maintainability.",
  "cv_summary": {"pr_auc_mean": 0.0, "pr_auc_std": 0.0, "recall_at_k_mean": 0.0},
  "test_evaluations": 0,
  "test_summary": {"pr_auc": null, "roc_auc": null, "recall_at_k": null, "precision_at_k": null, "brier": null},
  "fairness_summary_file": "reports/fairness/group_metrics.json",
  "explainability_files": ["reports/explainability/shap_global_bar.png"],
  "intended_use": "Decision support for voluntary, supportive adviser outreach after the first semester.",
  "non_use": "No automated or adverse decisions about admission, enrollment, scholarships, financial aid, grades, discipline, housing, or opportunities.",
  "disclaimer": "Scores are illustrative decision support, not causal, and require qualified human review."
}
```

## Rules

- Numeric fields above shown as `0`/`0.0`/`null` are placeholders; the writer MUST fill them
  from computed values. `model-card` fails if any remains at its placeholder value after
  `evaluate-test`.
- The app refuses to serve when `model_version != app.expected_model_version` or when
  `pipeline_sha256` does not match the file on disk.
- `test_evaluations` greater than 1 is surfaced in the model card as a note.
- No row-level data, identifiers, or sensitive-group raw values are stored in the manifest.
