# Student Success Navigator — local demo container (optional Step 8 / Milestone 10).
# Copies ONLY what the app reads: package, configs, persisted model + manifest, demo cohort, reports.
# Never copies raw, processed, evaluator-only, or local data (see .dockerignore and tests/unit/test_dockerignore.py).
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install -r requirements.txt && pip install -e .

COPY configs ./configs
COPY models ./models
COPY data/demo ./data/demo
COPY data/README.md ./data/README.md
COPY reports ./reports
RUN mkdir -p data/local && python -m ssn config validate

EXPOSE 8050
# bind to all interfaces inside the container; the host maps the port
CMD ["python", "-c", "from ssn.app.app import create_app; from ssn.config import load; cfg=load('configs/base.yaml', set_seeds=False); create_app(cfg).run(host='0.0.0.0', port=8050, debug=False)"]
