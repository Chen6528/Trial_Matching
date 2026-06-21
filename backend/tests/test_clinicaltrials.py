"""Unit tests for CT.gov field extraction (pure, no network).

`fetch_studies` uses curl_cffi (to clear Akamai bot detection), which respx can't intercept —
but the parsing it relies on, `parse_study`, is a pure dict->row function and is the part worth
covering. `parse_age` is exercised in test_scoring.py.
"""
from __future__ import annotations

from app.services.clinicaltrials import parse_study

_STUDY = {
    "protocolSection": {
        "identificationModule": {"nctId": "NCT12345678", "briefTitle": "A Study of X in NSCLC"},
        "statusModule": {"overallStatus": "RECRUITING"},
        "conditionsModule": {"conditions": ["Non-small Cell Lung Cancer", "EGFR"]},
        "eligibilityModule": {
            "sex": "ALL",
            "minimumAge": "18 Years",
            "maximumAge": "75 Years",
            "healthyVolunteers": "No",
            "eligibilityCriteria": "Inclusion Criteria:\n- ECOG 0-1\nExclusion:\n- Brain mets",
        },
    },
}


def test_parse_study_flattens_nested_fields():
    row = parse_study(_STUDY)
    assert row["nct_id"] == "NCT12345678"
    assert row["brief_title"] == "A Study of X in NSCLC"
    assert row["conditions"] == ["Non-small Cell Lung Cancer", "EGFR"]
    assert row["overall_status"] == "RECRUITING"
    assert row["sex"] == "ALL"
    assert row["min_age_years"] == 18.0
    assert row["max_age_years"] == 75.0
    assert row["healthy_volunteers"] is False  # coerced from "No"
    assert "ECOG" in row["eligibility_criteria"]
    assert row["raw_json"] is _STUDY  # full record kept for re-processing


def test_parse_study_handles_missing_modules():
    row = parse_study({})
    assert row["nct_id"] is None
    assert row["conditions"] == []
    assert row["overall_status"] is None
    assert row["min_age_years"] is None
    assert row["healthy_volunteers"] is None


def test_parse_study_coerces_healthy_volunteers_yes():
    study = {"protocolSection": {"eligibilityModule": {"healthyVolunteers": "Yes"}}}
    assert parse_study(study)["healthy_volunteers"] is True
