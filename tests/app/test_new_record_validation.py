from __future__ import annotations

from ssn.app.services.validation import validate


def _valid_form(fields):
    form = {}
    for f in fields:
        form[f.name] = f.options[0][0] if f.options else (f.lo if f.lo is not None else 1.0)
    return form


def test_form_fields_are_exactly_the_schema_and_first_semester_only(fixture_state):
    st = fixture_state
    names = {f.name for f in st.fields}
    assert names == set(st.bundle.allow.allowed_source)
    assert not any("2nd sem" in n for n in names)
    assert not names & set(st.bundle.allow.sensitive)
    assert {f.availability for f in st.fields} <= {"enrollment", "first_semester"}


def test_valid_submission_produces_one_row_frame(fixture_state):
    errors, frame = validate(_valid_form(fixture_state.fields), fixture_state.fields)
    assert errors == {} and frame is not None and len(frame) == 1
    assert list(frame.columns) == [f.name for f in fixture_state.fields]


def test_missing_field_is_reported_by_label(fixture_state):
    form = _valid_form(fixture_state.fields)
    f0 = fixture_state.fields[0]
    form[f0.name] = None
    errors, frame = validate(form, fixture_state.fields)
    assert frame is None and f0.name in errors and f0.label in errors[f0.name]


def test_out_of_range_numeric_rejected(fixture_state):
    numeric = next(f for f in fixture_state.fields if f.kind == "numeric" and f.hi is not None)
    form = _valid_form(fixture_state.fields)
    form[numeric.name] = numeric.hi + 1000
    errors, frame = validate(form, fixture_state.fields)
    assert frame is None and "between" in errors[numeric.name]


def test_undocumented_code_rejected(fixture_state):
    coded = next(f for f in fixture_state.fields if f.options)
    form = _valid_form(fixture_state.fields)
    form[coded.name] = 999999
    errors, frame = validate(form, fixture_state.fields)
    assert frame is None and "not a documented option" in errors[coded.name]


def test_unexpected_fields_rejected(fixture_state):
    form = _valid_form(fixture_state.fields)
    form["Curricular units 2nd sem (grade)"] = 12.0
    form["Gender"] = 1
    errors, frame = validate(form, fixture_state.fields)
    assert frame is None and "unexpected fields" in errors["_form"]
