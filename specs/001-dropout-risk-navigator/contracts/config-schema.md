# Contract: Configuration Schema (`configs/base.yaml` and `configs/models/*.yaml`)

Loaded and validated by `ssn.config.load(path)`. Missing required keys or wrong types raise
`ConfigError` with the offending key path. Unknown keys raise unless under `extra:`.

## `configs/base.yaml`

```yaml
project:
  name: student-success-navigator
  model_version: "1.0.0"            # semantic version; must match manifest when served

seed: 42                            # single seed propagated everywhere

paths:
  raw_csv: data/raw/data.csv
  processed_dir: data/processed
  demo_dir: data/demo
  evaluation_dir: data/evaluation   # evaluator-only
  local_dir: data/local             # Git-ignored runtime state
  data_dictionary: data/data_dictionary.md
  models_dir: models
  reports_dir: reports
  features_yaml: configs/features.yaml
  language_yaml: configs/language.yaml

data:
  expected_sha256: "<filled in M2>"  # of data/raw/data.csv
  target_column: Target
  target_positive_label: Dropout     # verified in PV-02
  target_expected_labels: [Dropout, Enrolled, Graduate]

split:
  test_size: 0.2
  stratify: true
  cv_folds: 5

capacity:
  per_week: 10                       # ILLUSTRATIVE students an adviser can contact per week (PV-10)
  window_weeks: 5                    # ILLUSTRATIVE outreach window
  k: 50                              # derived = per_week * window_weeks; loader validates equality
  window_sensitivity_weeks: [2, 5, 10]   # K sensitivity = per_week * each window
  illustrative: true                 # must be true; UI and reports read this flag for labels

threshold:
  rule: oof_quantile_for_capacity
  band_names: ["Priority outreach", "Check-in suggested", "Standard support"]
  middle_band_selection_rate_multiplier: 2.0

imbalance:
  primary: class_weight             # class_weight | smote
  compare_smote: true

selection:
  filter_method: mutual_info        # mutual_info | anova_f
  embedded_method: l1_logreg        # l1_logreg | tree_importance
  k_grid: [10, 15, 20, all]

pca:
  variance_threshold: 0.95
  compare_in_cv: true

fairness:
  attributes: [gender, age_band]    # gender requires verified encoding (PV-04)
  min_group_size: 30                # assumption; PV-07 finalises
  reference_group: largest
  age_bands: []                     # filled after PV-06; list of {name, lower, upper}

explain:
  method: shap                      # shap | permutation
  pdp_min_distinct_values: 10

app:
  host: 127.0.0.1
  port: 8050
  expected_model_version: "1.0.0"
  actions_db: data/local/actions.sqlite
  disclaimer_key: educational

report:
  reproduction_tolerance_file: docs/REPRODUCIBILITY.md
```

## `configs/models/<name>.yaml`

```yaml
name: hist_gb
estimator: sklearn.ensemble.HistGradientBoostingClassifier
params:
  class_weight: balanced
  early_stopping: true
  random_state: ${seed}             # substituted from base.yaml
search_space:
  learning_rate: {type: loguniform, low: 0.01, high: 0.3}
  max_leaf_nodes: {type: randint, low: 8, high: 64}
  min_samples_leaf: {type: randint, low: 10, high: 100}
  l2_regularization: {type: loguniform, low: 1e-4, high: 1.0}
n_iter: 40
use_selection: true
use_pca: false
```

Required model names for the capstone: `dummy`, `logreg`, `random_forest`, `hist_gb`. Optional:
`svm`, `xgboost`.

## `configs/language.yaml`

```yaml
prohibited_terms:
  - "at risk of failing"
  - "likely to drop out"
  - "problem student"
  - "failing student"
features:
  sem1_approval_rate:
    label: "First-semester course completion"
    higher_phrase: "completed a larger share of first-semester courses"
    lower_phrase: "completed a smaller share of first-semester courses"
    adviser_visible: true
  gender:
    label: "Gender"
    adviser_visible: false           # aggregate audit only
```

Every allow-listed and engineered feature MUST have an entry; `scan-language` fails otherwise.
