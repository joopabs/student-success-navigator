# Thin wrappers over `python -m ssn ...` (contract: specs/001-dropout-risk-navigator/contracts/cli.md)
PY ?= python
CFG ?= configs/base.yaml
SSN = $(PY) -m ssn

.PHONY: setup data eda select cv tune final explain fairness report app test lint secrets all

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

app:
	$(SSN) app --config $(CFG)

test:
	$(PY) -m pytest -q

lint:
	ruff check .

secrets:
	detect-secrets scan --exclude-lines '[0-9a-f]{64}' $$(git ls-files) | $(PY) -c "import sys,json; r=json.load(sys.stdin)['results']; [print(f, [x['type'] for x in v]) for f,v in r.items()]; sys.exit(1 if r else 0)"
	@echo "secrets scan clean"

all: data eda select cv tune final explain fairness report
