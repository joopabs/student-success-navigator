"""FR-066a: the scoring form must explain its inputs, from configuration rather than from the page.

The sourcing clause is the point. A future edit could easily write a friendlier definition straight
into the page, and it would look like an improvement while quietly asserting something about the
dataset that the dataset does not say. These check that every word shown comes from the allow-list
description or the adviser phrasing in configs/language.yaml.
"""

from __future__ import annotations

from ssn.app.pages.new_record import _hint, _meaning


def _numeric(state):
    return [f for f in state.fields if not f.options]


def test_every_numeric_field_is_explained(fixture_state):
    unexplained = [f.label for f in _numeric(fixture_state) if not _meaning(fixture_state, f)]
    assert not unexplained, unexplained


def test_explanations_are_sourced_not_authored(fixture_state):
    """Every fragment shown must appear in the allow-list description or in language.yaml."""
    for f in _numeric(fixture_state):
        text = _meaning(fixture_state, f)
        if not text:
            continue
        sourced = " ".join(
            [
                f.description or "",
                (fixture_state.rules.features.get(f.name) or {}).get("higher_phrase") or "",
            ]
        ).lower()
        # strip the only connective the page itself contributes
        remainder = text.lower().replace("higher:", " ")
        for word in (w.strip(".,;()%") for w in remainder.split()):
            if len(word) < 4:  # skip articles and short connectives
                continue
            assert word in sourced, (f.label, word)


def test_direction_matches_the_review_page_phrasing(fixture_state):
    """The form and the explanations must describe a field the same way, not paraphrase it."""
    for f in _numeric(fixture_state):
        phrase = (fixture_state.rules.features.get(f.name) or {}).get("higher_phrase")
        if phrase and _meaning(fixture_state, f):
            assert phrase in _meaning(fixture_state, f), f.label


def test_coded_fields_are_exempt(fixture_state):
    """Their dropdowns already decode them, and 'higher' is meaningless for a category code."""
    coded = [f for f in fixture_state.fields if f.options]
    assert coded, "fixture should include at least one coded field"
    for f in coded:
        assert _meaning(fixture_state, f) == ""
        assert _hint(fixture_state, f).children is None


def test_hint_states_range_training_range_and_typical_value(fixture_state):
    """The fixture carries no medians or observed ranges, so supply them and check they surface."""
    from dataclasses import replace

    field = _numeric(fixture_state)[0]
    state = replace(
        fixture_state,
        reference={field.name: 12.5},
        observed_ranges={field.name: {"min": 2.0, "max": 9.0}},
    )
    hint = _hint(state, field).children
    assert "typical 12.5" in hint, hint
    assert "training data 2-9" in hint, hint
    assert "accepts" in hint, hint


def test_observed_range_is_omitted_when_it_equals_the_accepted_range(fixture_state):
    """Repeating the same numbers twice is noise, not information."""
    from dataclasses import replace

    field = _numeric(fixture_state)[0]
    state = replace(
        fixture_state, observed_ranges={field.name: {"min": field.lo, "max": field.hi}}
    )
    assert "training data" not in (_hint(state, field).children or "")
