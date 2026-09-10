# Rubric Evidence Map

**Generated:** 2026-09-10 19:02 UTC by `python -m ssn rubric-map`. Criteria and points from
`CAPSTONE_BRIEF.md` section 5 (total 100, bonus included). Links are relative to `reports/`; an item marked
(pending) does not exist yet in the repository.

| Criterion | Points | Evidence |
|---|---|---|
| 1: Problem Understanding & Framing | 10 | [`reports/final_report.md#1-problem-understanding-and-framing`](../reports/final_report.md#1-problem-understanding-and-framing)<br>[`PROJECT_DECISIONS.md`](../PROJECT_DECISIONS.md)<br>[`reports/tables/test_recall_precision_at_k.csv`](../reports/tables/test_recall_precision_at_k.csv)<br>[`configs/base.yaml`](../configs/base.yaml) |
| Step 2: Data Collection & Understanding | 10 | [`data/README.md`](../data/README.md)<br>[`reports/data_overview.md`](../reports/data_overview.md)<br>[`data/data_dictionary.md`](../data/data_dictionary.md)<br>[`reports/tables/profile_columns.csv`](../reports/tables/profile_columns.csv)<br>[`reports/tables/profile_target.csv`](../reports/tables/profile_target.csv)<br>[`notebooks/01_data_profiling.ipynb`](../notebooks/01_data_profiling.ipynb) |
| Step 3: Data Preprocessing, EDA & Feature Engineering | 10 | [`reports/eda_feature_engineering_report.md`](../reports/eda_feature_engineering_report.md)<br>[`reports/tables/clean_before_after.csv`](../reports/tables/clean_before_after.csv)<br>[`reports/figures/eda_correlation_spearman.png`](../reports/figures/eda_correlation_spearman.png)<br>[`reports/tables/selection_decision.json`](../reports/tables/selection_decision.json)<br>[`reports/tables/pca_vs_nopca_cv.csv`](../reports/tables/pca_vs_nopca_cv.csv)<br>[`src/ssn/features/engineering.py`](../src/ssn/features/engineering.py)<br>[`notebooks/02_eda_feature_engineering.ipynb`](../notebooks/02_eda_feature_engineering.ipynb)<br>[`notebooks/03_feature_selection_pca.ipynb`](../notebooks/03_feature_selection_pca.ipynb) |
| Step 4: Model Implementation & Comparison | 20 | [`reports/model_comparison_cv.md`](../reports/model_comparison_cv.md)<br>[`reports/model_selection_and_evaluation.md`](../reports/model_selection_and_evaluation.md)<br>[`reports/tables/cv_comparison.csv`](../reports/tables/cv_comparison.csv)<br>[`reports/tables/selection_matrix_ranked.csv`](../reports/tables/selection_matrix_ranked.csv)<br>[`reports/tables/test_metrics_all_models.csv`](../reports/tables/test_metrics_all_models.csv)<br>[`models/manifest.json`](../models/manifest.json)<br>[`docs/REPRODUCIBILITY.md`](../docs/REPRODUCIBILITY.md)<br>[`notebooks/04_model_comparison.ipynb`](../notebooks/04_model_comparison.ipynb) |
| Step 5: Critical Thinking, Ethical AI & Bias Auditing | 20 | [`reports/bias_fairness_analysis.md`](../reports/bias_fairness_analysis.md)<br>[`reports/limitations.md`](../reports/limitations.md)<br>[`reports/model_card.md`](../reports/model_card.md)<br>[`reports/explainability/shap_global_bar.png`](../reports/explainability/shap_global_bar.png)<br>[`reports/explainability/shap_local_examples.json`](../reports/explainability/shap_local_examples.json)<br>[`reports/fairness/group_metrics.csv`](../reports/fairness/group_metrics.csv)<br>[`reports/fairness/mitigation_comparison.csv`](../reports/fairness/mitigation_comparison.csv)<br>[`notebooks/05_explainability_fairness.ipynb`](../notebooks/05_explainability_fairness.ipynb) |
| Step 6: Final Presentation & Communication | 10 | [`reports/decks/technical_deck.slides.html`](../reports/decks/technical_deck.slides.html)<br>[`notebooks/90_technical_deck.ipynb`](../notebooks/90_technical_deck.ipynb)<br>[`reports/decks/business_deck_outline.md`](../reports/decks/business_deck_outline.md)<br>[`reports/decks/business_deck.pptx`](../reports/decks/business_deck.pptx) |
| Step 7: GitHub Profile & Upload | 15 | [`README.md`](../README.md)<br>[`requirements.txt`](../requirements.txt)<br>[`reports/final_report.md`](../reports/final_report.md)<br>[`tests`](../tests)<br>[`.github/workflows/ci.yml`](../.github/workflows/ci.yml)<br>[`LICENSE`](../LICENSE) |
| Bonus: Creative and well-presented submission | 5 | [`docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md)<br>[`docs/MLOPS.md`](../docs/MLOPS.md)<br>[`docs/GENAI_USE.md`](../docs/GENAI_USE.md)<br>[`src/ssn/app`](../src/ssn/app)<br>[`reports/decks/demo.gif`](../reports/decks/demo.gif) |
| **Total** | **100** | |

<!-- BEGIN NOTES -->
_Hand-written notes (e.g. submission checklist completion) go here and survive regeneration._

### Constitutional quality gates G1–G10 — evidence

The constitution requires that "Gate evidence MUST be linked from the final report's rubric map"
(`.specify/memory/constitution.md`, Quality Gates & Definition of Done). Each gate below links the
artifacts that satisfy it. All paths are relative to the repository root.

| Gate | Phase | Evidence | Status |
|---|---|---|---|
| G1 | Framing | [`reports/final_report.md`](../reports/final_report.md) §1 · [`specs/001-dropout-risk-navigator/spec.md`](../specs/001-dropout-risk-navigator/spec.md) · [`PROJECT_DECISIONS.md`](../PROJECT_DECISIONS.md) | pass |
| G2 | Data | [`data/README.md`](../data/README.md) · [`reports/data_overview.md`](../reports/data_overview.md) · `reports/tables/profile_columns.csv` · `reports/tables/profile_categorical_values.csv` · `tests/unit/test_schema.py` | pass |
| G3 | Leakage | [`configs/features.yaml`](../configs/features.yaml) allow-list · `tests/unit/test_allowlist.py` · `tests/unit/test_features_yaml_complete.py` · `tests/unit/test_pca_fit_isolation.py` · `tests/unit/test_selection_in_pipeline.py` | pass |
| G4 | Preprocessing & EDA | [`reports/eda_feature_engineering_report.md`](../reports/eda_feature_engineering_report.md) · `reports/tables/clean_before_after.csv` · `reports/tables/pca_explained_variance.csv` · `reports/figures/` | pass |
| G5 | Modelling | [`reports/model_comparison_cv.md`](../reports/model_comparison_cv.md) · [`reports/model_selection_and_evaluation.md`](../reports/model_selection_and_evaluation.md) · `reports/tables/cv_comparison.csv` · `reports/tables/test_metrics_all_models.csv` · `reports/figures/test_pr_curve.png` | pass |
| G6 | Explainability | [`reports/explainability/`](../reports/explainability) — `reports/explainability/shap_global_importance.csv`, `reports/explainability/shap_global_bar.png`, `reports/explainability/pdp_ice_*.png`, `reports/explainability/method.json` | pass |
| G7 | Fairness | [`reports/bias_fairness_analysis.md`](../reports/bias_fairness_analysis.md) · `reports/fairness/group_metrics.csv` · `reports/fairness/selection_rates.png` · `tests/unit/test_groups_min_size.py` · `tests/unit/test_language_no_sensitive_reasons.py` | pass |
| G8 | Application | [`src/ssn/app`](../src/ssn/app) · [`docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md) · [`reports/model_card.md`](../reports/model_card.md) · `tests/app/test_no_labels_rendered.py`, `tests/app/test_queue_to_action_interactions.py`, `tests/app/test_version_check.py` · [`reports/decks/demo.gif`](../reports/decks/demo.gif) | pass |
| G9 | Reproducibility | [`docs/REPRODUCIBILITY.md`](../docs/REPRODUCIBILITY.md) · `models/manifest.json` · `tests/integration/test_reproduce_fixture.py` · `tests/unit/test_persist_manifest.py` | pass |
| G10 | Communication & Repo | [`reports/decks/technical_deck.slides.html`](../reports/decks/technical_deck.slides.html) (12 slides) · [`reports/decks/business_deck.pptx`](../reports/decks/business_deck.pptx) (10 slides) · [`reports/final_report.md`](../reports/final_report.md) · this rubric map · [`README.md`](../README.md) | pass |

The Definition of Done additionally requires that the repository be public with no secrets or private
data. Satisfied on 2026-09-11: the repository is public at https://github.com/joopabs/student-success-navigator,
published after a final check confirming no tracked private files, no secrets and no model binaries (T092).

### Pre-publication checklist — run 2026-09-11 (quickstart section 11, T092)

| Gate | Command | Result |
|---|---|---|
| No private file tracked | `git ls-files \| grep -Ei 'data/…\|.env\|.sqlite\|Pillar5'` | clean |
| Secrets | `make secrets` | clean |
| Lint | `ruff check .` | clean |
| Tests | `pytest -q` | 197 passed |
| Adviser-facing language | `python -m ssn scan-language` | clean, 58 files |
| History | `git log --oneline` | 24 commits, one logical change each, `<type>: <description>` throughout |

### Submission package

`make submission` writes the upload set into `submission/` (Git-ignored) under the required
`Your_Name_Assignment name` pattern: the report as `.doc` and `.html`, the technical deck
(12 slides), the business deck (10 slides), the code archive, and the repository link. Both
`.doc` and `.pptx` are approved formats under the brief's section 8.

### Demo media (T091, complete)

`reports/decks/demo.gif` — 8 frames covering the six adviser pages, the acknowledgement modal and the
version-mismatch blocking page. Generated in process by `scripts/render_demo_gif.py` (`make demo`):
`route()` returns the same component tree the browser renders, so every frame carries the app's real
text and real numbers. The script asserts that no outcome label appears on any record-bearing frame
and refuses to write the file if one does, which makes the privacy claim checkable rather than
eyeballed. The Model Card frame is exempt and documented as such: it states the target encoding and
carries no record data.

### Status

All 92 tasks are complete and every gate above passes. The repository is public, the submission package
is built by `make submission` (run it after the final commit — it archives `HEAD`), and the Definition of
Done in the constitution is met in full.
<!-- END NOTES -->
