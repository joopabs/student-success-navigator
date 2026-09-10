# Generative AI Use in This Project

**Status: Generative AI was used, extensively, as a development assistant.** This note records what was used, for
what, how the work was reviewed, what was deliberately kept away from it, and its limitations, as required by the
optional Step 9 of the assignment and by project rules (`PROJECT_DECISIONS.md`, constitution Principle III).

## Tool

- **Claude Code** (Anthropic), model Claude Fable 5.1, run as a command-line agent inside this repository between
  2026-09-09 and 2026-09-10, with **Spec Kit** slash commands (`/speckit-constitution`, `/speckit-specify`,
  `/speckit-plan`, `/speckit-tasks`, `/speckit-analyze`, `/speckit-implement`) as the working method.
- No other generative model was used. No LLM is part of the shipped software: the Student Success Navigator app,
  the pipeline, and the reports contain no model calls, no generated text at runtime, and no "AI explanations";
  explanations come from SHAP on the trained model.

## What it was used for

| Area | How Generative AI was used | Human review |
|---|---|---|
| Governance | Drafted the constitution (12 principles, 10 gates) from the author's instructions; extracted the rubric from the course PDF into `CAPSTONE_BRIEF.md` without adding requirements | Author read and amended (e.g. bonus inside the 100, target rating band, optional steps), then ratified |
| Specification and planning | Drafted `spec.md`, `plan.md`, `research.md`, data model, contracts, and the 92-task list; ran a cross-artifact analysis that found three HIGH inconsistencies, which the author approved fixing | Author chose the repository layout, the sensitive-attribute policy, the capacity framing, the licence, and pulled CI forward |
| Code | Wrote the pipeline package, tests, notebooks, CLI, and Dash app following the approved plan | Every milestone ended with lint, tests, a language scan, and a privacy dry-run; the author committed and pushed each milestone after reviewing the report |
| Documentation and reports | Generated the data overview, dictionary, EDA report, model comparison, selection report, bias and fairness analysis, limitations, model card, rubric map, final report, slide deck, and business-deck outline — **every number is read from a file produced by the pipeline**, and a scanner blocks prohibited or unlabelled business language | Author reviewed wording and decisions (e.g. age bands, K = 10 per week × 5 weeks) |
| Verification of facts | Fetched the UCI dataset page and API to verify licence (CC BY 4.0), citation, and every categorical encoding; recorded when a source (the MDPI article) could not be retrieved rather than guessing | Recorded in `data/README.md` as an open item |

## Example prompts

The prompts were the Spec Kit commands with the author's requirements as arguments, for example:

- `/speckit-constitution … The constitution must enforce: leakage-safe temporal feature availability … no
  sensitive/private data or credentials in Git … Student Success Navigator must be a human-in-the-loop
  support-prioritization tool …`
- `/speckit-implement Implement only Milestone 6: tuning, capacity-aware threshold selection, final held-out
  evaluation, calibration, and artifact persistence. … Evaluate the chosen final model once on the held-out test
  data. … Clearly distinguish measured metrics from illustrative business outcomes. Do not claim production
  readiness or causal impact.`
- `/speckit-implement Implement only Milestone 9 … Do not use gender, age, nationality, or socioeconomic
  variables as reasons to recommend action in the adviser UI … Do not invent model metrics, SHAP values, or
  fairness results; load existing artifacts/reports.`

The full command history is visible in the commit sequence (one commit per milestone) and in the task list
`specs/001-dropout-risk-navigator/tasks.md`.

## Data handling

- The dataset is public and de-identified (UCI 697, CC BY 4.0). It was downloaded and processed locally by
  the pipeline. During acquisition the CSV header and its first data row appeared in the assistant's tool
  output for format inspection; aggregate profile tables appeared thereafter. This is consistent with the
  project rule that raw records may only be exposed to an external service when the data are confirmed public
  and de-identified (spec FR-021). No private, institutional, or student-identifying data exists in this project.
- No credentials, tokens, or personal data were shared with the assistant; the repository's secrets scan runs
  in CI.

## Guardrails that applied to the assistant's output

- Numbers in documents must come from files under `reports/` or `models/` (no typed results); the model card
  refuses to render on placeholders or on an unqualified fairness claim.
- Tests written alongside the code assert leakage safety, privacy of adviser pages, hand-computed metric values,
  artifact integrity, and the acknowledgement flow; 195 tests pass in CI.
- The author retained every decision with ethical or scope weight and reviewed each milestone before it was
  committed.

## Limitations of this use

- Generated prose can be fluent while wrong; the mitigation was to generate every quantitative statement from
  data files and to run automated scans, not to trust the text.
- The assistant occasionally introduced defects that tests caught (a phrase-direction bug in local explanations,
  a scanner false positive on CSS, a shell-quoting mistake in the reproduction run); these are recorded in the
  milestone reports and were fixed before commit.
- Use of an assistant does not transfer responsibility: the design choices, their justification, and any errors
  remaining in this repository are the author's.
