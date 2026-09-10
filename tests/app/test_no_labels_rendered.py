from __future__ import annotations

import re

import pytest

from ssn.app.app import create_app, route
from ssn.explain import language as L
from tests.app.conftest import render_json

RULES = L.load("configs/language.yaml")
OUTCOME_TOKENS = ["is_dropout", '"Target"', "Graduate", "Enrolled"]
SENSITIVE_LABELS = [
    "Gender",
    "Age at enrollment",
    "Nacionality",
    "Marital status",
    "International",
    "Educational special needs",
    "age_band",
]


def _render(state, path) -> str:
    return render_json(route(state, path))


@pytest.fixture(scope="module")
def app(fixture_state):
    return create_app(fixture_state.cfg, state=fixture_state)


def _adviser_paths(state):
    rid = state.ranked.iloc[0]["record_id"]
    return ["/", "/queue", f"/review/{rid}", "/score"]


def test_adviser_pages_never_show_outcomes_or_identifiers(fixture_state, app):
    for path in _adviser_paths(fixture_state):
        text = _render(fixture_state, path)
        for tok in OUTCOME_TOKENS:
            assert tok not in text, (path, tok)
        assert "Dropout" not in text.replace("Dropout and Academic Success", ""), path
        assert "@" not in text.replace("Recall@K", "").replace("Precision@K", ""), path  # no emails


def test_adviser_pages_never_show_sensitive_attributes(fixture_state, app):
    for path in _adviser_paths(fixture_state):
        text = _render(fixture_state, path)
        for lab in SENSITIVE_LABELS:
            # a sensitive COLUMN would appear as a quoted JSON string (field id, header, label);
            # documented option labels such as "International student (bachelor)" are not columns
            assert not re.search(rf'"{re.escape(lab)}"', text), (path, lab)


def test_all_pages_pass_prohibited_term_scan(fixture_state, app):
    rid = fixture_state.ranked.iloc[0]["record_id"]
    for path in ["/", "/queue", f"/review/{rid}", "/score", "/equity", "/model-card"]:
        text = _render(fixture_state, path).lower()
        for term in RULES.prohibited_terms:
            assert term not in text, (path, term)


def test_disclaimer_and_version_present_on_every_page(fixture_state, app):
    rid = fixture_state.ranked.iloc[0]["record_id"]
    for path in ["/", "/queue", f"/review/{rid}", "/score", "/equity", "/model-card"]:
        text = _render(fixture_state, path)
        assert "Advisory only" in text, path
    layout = render_json(app.layout)
    assert f"Model version {fixture_state.bundle.model_version}" in layout


def test_queue_shows_exactly_k_rows_and_retrospective_label(fixture_state, app):
    from ssn.app.pages.support_queue import table

    text = render_json(table(fixture_state, 20))
    assert text.count('"type": "open-ack"') == 20
    assert "Retrospective evaluation" in text
    text_big = render_json(table(fixture_state, 10_000))
    assert "exceeds the cohort size" in text_big


def test_equity_page_flags_small_groups(fixture_state, app):
    text = _render(fixture_state, "/equity")
    assert "small group" in text and "n ≥ min" in text
