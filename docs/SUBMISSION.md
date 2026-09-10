# Submission Checklist

Course instructions (`CAPSTONE_BRIEF.md` section 8): collate the textual responses in an approved format (.pdf, .doc,
.pptx, .ppt), submit the coding files, rename files as `Your_Name_Assignment name`, then use Start Assignment →
upload → Submit Assignment.

## Files to upload (packaged by `make submission` into `submission/`, Git-ignored)

| File | Source | Status |
|---|---|---|
| `Julius_Pabular_Pillar5_Capstone_Project_Report.pdf` | `reports/final_report.pdf`, rendered from the HTML by `scripts/html_to_pdf.py` (xhtml2pdf; pandoc not installed) | packaged |
| `Julius_Pabular_Pillar5_Capstone_Project_Report.html` | `reports/final_report.html` | packaged |
| `Julius_Pabular_Pillar5_Capstone_Project_Technical_Deck.html` | `reports/decks/technical_deck.slides.html` (12 slides) | packaged |
| `Julius_Pabular_Pillar5_Capstone_Project_Business_Deck.pptx` | `reports/decks/business_deck.pptx` (10 slides) | packaged |
| `Julius_Pabular_Pillar5_Capstone_Project_Code.zip` | `git archive HEAD` (code, configs, reports, tests; no data or model binaries) | packaged |
| `Julius_Pabular_Pillar5_Capstone_Project_Links.txt` | GitHub repository URL | packaged |

The target prefers `reports/final_report.pdf` when it exists and otherwise falls back to a `.doc` produced by
macOS `textutil`; both are approved formats. Regenerate the PDF with `scripts/html_to_pdf.py` after editing
the report.

## Pre-publication gate (quickstart section 11)

```bash
git ls-files | grep -v '\.gitkeep$' | grep -Ei 'data/(raw|interim|processed|demo|evaluation|local)/|\.env$|\.sqlite|Pillar5' && echo "STOP" || echo clean
make secrets && make lint && make test
python -m ssn scan-language --paths reports README.md docs notebooks src/ssn/app
git log --oneline            # one logical change per commit, imperative messages
```

Then, and only then, make the repository public:

```bash
gh repo edit joopabs/student-success-navigator --visibility public --accept-visibility-change-consequences
```

## Demo media (T091)

`reports/decks/demo.gif` is generated rather than recorded. `scripts/render_demo_gif.py` drives the app in
process — `route()` returns the same component tree the browser renders — and draws each state with Pillow,
so no browser and no screen-recording permission are involved:

```bash
.venv/bin/python scripts/render_demo_gif.py
```

Eight frames: the six adviser pages, the acknowledgement modal, and the version-mismatch blocking page. The
script asserts that no outcome label appears on any record-bearing frame and refuses to write the GIF if one
does. The Model Card frame is exempt and says so: it documents the target encoding and carries no record data.

To record a live screencast instead, run `python -m ssn app` and use Cmd+Shift+5 on macOS: Overview → Support
Queue (change K) → a Student Review → "Record support action" (Save stays disabled until the acknowledgement
is ticked; save) → New Record Scoring (submit empty for validation, then a valid record) → Equity Dashboard →
Model Card, then the blocking page via `python -m ssn app --config /tmp/mismatch.yaml` (`docs/DEPLOYMENT.md` §6).
Link it from `docs/DEPLOYMENT.md` and `README.md`.
