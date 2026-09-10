# Submission Checklist

Course instructions (`CAPSTONE_BRIEF.md` section 8): collate the textual responses in an approved format (.pdf, .doc,
.pptx, .ppt), submit the coding files, rename files as `Your_Name_Assignment name`, then use Start Assignment →
upload → Submit Assignment.

## Files to upload (packaged by `make submission` into `submission/`, Git-ignored)

| File | Source | Status |
|---|---|---|
| `Julius_Pabular_Pillar5_Capstone_Project_Report.doc` | `reports/final_report.html` converted by `textutil` (pandoc not installed); `.doc` is an approved format | packaged |
| `Julius_Pabular_Pillar5_Capstone_Project_Report.html` | `reports/final_report.html` | packaged |
| `Julius_Pabular_Pillar5_Capstone_Project_Technical_Deck.html` | `reports/decks/technical_deck.slides.html` (12 slides) | packaged |
| `Julius_Pabular_Pillar5_Capstone_Project_Business_Deck.pptx` | `reports/decks/business_deck.pptx` (10 slides) | packaged |
| `Julius_Pabular_Pillar5_Capstone_Project_Code.zip` | `git archive HEAD` (code, configs, reports, tests; no data or model binaries) | packaged |
| `Julius_Pabular_Pillar5_Capstone_Project_Links.txt` | GitHub repository URL | packaged |

If a PDF is preferred over the `.doc`, open the packaged `.doc` in Word and export to PDF, then re-run
`make submission` with `reports/final_report.pdf` in place — the target prefers a PDF when one exists.

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

## Demo media (T091, manual)

Record `reports/decks/demo.gif` (or a screencast and link it in `docs/DEPLOYMENT.md` and `README.md`):

1. `python -m ssn app`, open http://127.0.0.1:8050.
2. macOS: Cmd+Shift+5 → record a selected window; visit Overview → Support Queue (change K) → a Student Review →
   "Record support action" (show Save disabled until the acknowledgement is ticked; save) → New Record Scoring
   (submit empty for validation, then a valid record) → Equity Dashboard → Model Card.
3. Show the blocking page: `python -m ssn app --config /tmp/mismatch.yaml` (see `docs/DEPLOYMENT.md` §6).
4. Convert to GIF (e.g. `ffmpeg -i demo.mov -vf "fps=8,scale=1000:-1" reports/decks/demo.gif`) and check no
   outcome label or identifier is visible in the recording (none exist on adviser pages by design).
