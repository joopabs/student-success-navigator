from __future__ import annotations

from ssn.explain import language as L
from ssn.features import allowlist as al

RULES = L.load("configs/language.yaml")
ALLOW = al.load("configs/features.yaml")


def test_every_allowlisted_and_engineered_feature_has_an_entry():
    assert L.missing_language_entries(RULES, ALLOW) == []


def test_sensitive_attributes_are_never_adviser_visible():
    for s in list(ALLOW.sensitive) + ["age_band"]:
        assert s in RULES.features and RULES.features[s]["adviser_visible"] is False


def test_render_local_drops_sensitive_and_orders_by_input():
    contributions = [
        {"feature": "Gender", "shap": 0.9, "value": 1},
        {"feature": "Curricular units 1st sem (approved)", "shap": 0.4, "value": 1},
        {"feature": "Age at enrollment", "shap": 0.3, "value": 40},
        {"feature": "sem1_any_approved", "shap": -0.2, "value": 1},
    ]
    out = L.render_local(
        contributions, RULES, reference={"Curricular units 1st sem (approved)": 5.0}
    )
    labels = [o["label"] for o in out]
    assert "Gender" not in labels and "Age at enrollment" not in labels and "age_band" not in labels
    assert labels == ["First-semester units passed", "Passed at least one unit"]
    text = " ".join(o["phrase"] for o in out).lower()
    for term in RULES.prohibited_terms:
        assert term not in text


def test_numeric_phrase_uses_training_median_not_shap_sign():
    c = [{"feature": "Curricular units 1st sem (approved)", "shap": 0.5, "value": 1}]
    low = L.render_local(c, RULES, reference={"Curricular units 1st sem (approved)": 5.0})[0]
    assert (
        low["phrase"] == "passed fewer first-semester units"
        and low["direction"] == "raises support priority"
    )
    c = [{"feature": "Curricular units 1st sem (approved)", "shap": -0.5, "value": 8}]
    high = L.render_local(c, RULES, reference={"Curricular units 1st sem (approved)": 5.0})[0]
    assert (
        high["phrase"] == "passed more first-semester units"
        and high["direction"] == "lowers support priority"
    )


def test_binary_and_categorical_phrases():
    b = L.render_local([{"feature": "Displaced", "shap": 0.1, "value": 0}], RULES)[0]
    assert b["phrase"] == "is studying in their home region"
    c = L.render_local([{"feature": "Course", "shap": 0.2, "value": 9130}], RULES)[0]
    assert "more often needed support" in c["phrase"]
    c2 = L.render_local([{"feature": "Course", "shap": -0.2, "value": 9500}], RULES)[0]
    assert "less often needed support" in c2["phrase"]


def test_rendered_phrases_pass_the_prohibited_term_scanner():
    for meta in RULES.features.values():
        for key in ("label", "higher_phrase", "lower_phrase"):
            if key in meta:
                assert L.scan_text(meta[key], RULES) == [], meta[key]
