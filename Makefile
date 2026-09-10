# Thin wrappers over `python -m ssn ...` (contract: specs/001-dropout-risk-navigator/contracts/cli.md)
PY ?= python
CFG ?= configs/base.yaml
SSN = $(PY) -m ssn

.PHONY: setup data eda select cv tune final explain fairness report report-export demo app test lint secrets submission all

setup:
	$(PY) -m pip install -r requirements.txt -r requirements-dev.txt
	$(PY) -m pip install -e .

data:
	$(SSN) data download --config $(CFG)
	$(SSN) data validate --config $(CFG)
	$(SSN) data profile --config $(CFG)
	$(SSN) data clean --config $(CFG)
	$(SSN) data split --config $(CFG)

eda:
	$(SSN) eda --config $(CFG)

select:
	$(SSN) select --config $(CFG)
	$(SSN) pca --config $(CFG)

cv:
	$(SSN) train-cv --config $(CFG) --models dummy logreg random_forest hist_gb

tune:
	$(SSN) tune --config $(CFG) --models logreg random_forest hist_gb

final:
	$(SSN) select-model --config $(CFG)
	$(SSN) calibrate --config $(CFG)
	$(SSN) threshold --config $(CFG)
	$(SSN) fit-final --config $(CFG)
	$(SSN) evaluate-test --config $(CFG)

explain:
	$(SSN) explain --config $(CFG)

fairness:
	$(SSN) fairness audit --config $(CFG)
	$(SSN) fairness mitigate --config $(CFG)

report:
	$(SSN) model-card --config $(CFG)
	$(SSN) rubric-map --config $(CFG)
	$(SSN) scan-language --paths reports README.md docs

report-export:
	$(PY) scripts/md_to_html.py reports/final_report.md reports/final_report.html
	@$(PY) -c "import xhtml2pdf" 2>/dev/null \
		&& $(PY) scripts/html_to_pdf.py reports/final_report.html reports/final_report.pdf \
		|| echo "note: xhtml2pdf not installed; keeping the existing reports/final_report.pdf (see scripts/html_to_pdf.py)"

demo:
	$(PY) scripts/render_demo_gif.py reports/decks/demo.gif

app:
	$(SSN) app --config $(CFG)

test:
	$(PY) -m pytest -q

lint:
	ruff check .

secrets:
	detect-secrets scan --exclude-lines '[0-9a-f]{40,64}' $$(git ls-files) | $(PY) -c "import sys,json; r=json.load(sys.stdin)['results']; [print(f, [x['type'] for x in v]) for f,v in r.items()]; sys.exit(1 if r else 0)"
	@echo "secrets scan clean"

# Package the submission files with the course naming pattern (Your_Name_Assignment name). Git-ignored output.
NAME ?= Julius_Pabular
ASSIGNMENT ?= Pillar5_Capstone_Project
submission:
	rm -rf submission && mkdir -p submission
	cp reports/final_report.html submission/$(NAME)_$(ASSIGNMENT)_Report.html
	@if [ -f reports/final_report.pdf ]; then \
		cp reports/final_report.pdf submission/$(NAME)_$(ASSIGNMENT)_Report.pdf; \
	elif command -v textutil >/dev/null 2>&1; then \
		textutil -convert doc -output submission/$(NAME)_$(ASSIGNMENT)_Report.doc reports/final_report.html; \
		echo "note: no reports/final_report.pdf; packaged .doc via textutil (.doc is an approved format)"; \
	else \
		echo "note: reports/final_report.pdf not found (print reports/final_report.html to PDF)"; \
	fi
	cp reports/decks/technical_deck.slides.html submission/$(NAME)_$(ASSIGNMENT)_Technical_Deck.html
	@test -f reports/decks/business_deck.pptx && cp reports/decks/business_deck.pptx submission/$(NAME)_$(ASSIGNMENT)_Business_Deck.pptx || echo "note: reports/decks/business_deck.pptx not found (assemble from the outline)"
	git archive --format=zip -o submission/$(NAME)_$(ASSIGNMENT)_Code.zip HEAD
	@echo "GitHub repository: https://github.com/joopabs/student-success-navigator" > submission/$(NAME)_$(ASSIGNMENT)_Links.txt
	@ls -la submission

all: data eda select cv tune final explain fairness report
