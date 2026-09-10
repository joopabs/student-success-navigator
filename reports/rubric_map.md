# Rubric Evidence Map

**Generated:** 2026-09-10 08:54 UTC by `python -m ssn rubric-map`. Criteria and points from
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
| Bonus: Creative and well-presented submission | 5 | [`docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md)<br>[`docs/MLOPS.md`](../docs/MLOPS.md)<br>[`docs/GENAI_USE.md`](../docs/GENAI_USE.md)<br>[`src/ssn/app`](../src/ssn/app) |
| **Total** | **100** | |

<!-- BEGIN NOTES -->
_Hand-written notes (e.g. submission checklist completion) go here and survive regeneration._

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

### Open at the time of writing

- **T091 — demo recording.** `reports/decks/demo.gif` is produced by hand; steps are in
  `docs/SUBMISSION.md`. No browser automation is available in this environment.
- **T092 — repository visibility.** The repository is still private, pending the owner's
  decision to publish. Every gate above passes, so publishing is unblocked on the technical side.
<!-- END NOTES -->
