"""Integration test for POST /api/match.

Exercises the real route orchestration + the deterministic scoring/ranking trust boundary,
with the provider-backed seams (embed / shortlist / load_criteria / reasoning) mocked. No
credentials or network, so it runs in CI.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api import routes_match as rm
from app.main import app
from app.models.results import CriterionVerdict
from app.models.trial import Criterion

# Each fake trial's criteria carry their intended verdict in `text`; the fake reasoning pass
# echoes that back as the status, so the REAL scoring.aggregate decides eligibility + confidence.
_STATUS_BY_TEXT = {"MET": "met", "NOT_MET": "not_met", "UNKNOWN": "unknown"}

_CRITERIA: dict[str, list[tuple[str, str]]] = {
    "NCT-A": [("inclusion", "MET"), ("exclusion", "NOT_MET")],   # all good -> likely_eligible 1.0
    "NCT-B": [("inclusion", "MET"), ("inclusion", "NOT_MET")],   # failed inclusion -> ineligible
    "NCT-C": [("inclusion", "MET"), ("inclusion", "UNKNOWN")],   # missing data -> needs_more_info 0.5
}

_SHORTLIST = [
    {"nct_id": "NCT-A", "brief_title": "Trial A", "similarity": 0.91},
    {"nct_id": "NCT-B", "brief_title": "Trial B", "similarity": 0.88},
    {"nct_id": "NCT-C", "brief_title": "Trial C", "similarity": 0.85},
]

_PROFILE = {"age": 62, "sex": "MALE", "condition": "non-small cell lung cancer"}


@pytest.fixture
def patched(monkeypatch):
    async def fake_embed(text):
        return [0.1, 0.2, 0.3]

    async def fake_shortlist(profile, embedding, match_count=None):
        return _SHORTLIST

    async def fake_load_criteria(nct_ids):
        return {
            nct: [Criterion(type=t, category="other", text=txt) for t, txt in _CRITERIA[nct]]
            for nct in nct_ids
        }

    async def fake_evaluate(patient_text, criteria):
        return [
            CriterionVerdict(type=c.type, text=c.text, status=_STATUS_BY_TEXT[c.text], reason="t")
            for c in criteria
        ]

    monkeypatch.setattr(rm, "embed_text", fake_embed)
    monkeypatch.setattr(rm, "shortlist", fake_shortlist)
    monkeypatch.setattr(rm, "load_criteria", fake_load_criteria)
    monkeypatch.setattr(rm, "evaluate_trial", fake_evaluate)


def test_match_ranks_and_scores(patched):
    client = TestClient(app)
    resp = client.post("/api/match", json=_PROFILE)
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 3  # one entry per shortlisted trial

    by_id = {r["nct_id"]: r for r in results}
    # eligibility + confidence are decided by the real scoring layer, not the (mocked) model.
    assert by_id["NCT-A"]["eligibility"] == "likely_eligible"
    assert by_id["NCT-A"]["confidence"] == 1.0
    assert by_id["NCT-B"]["eligibility"] == "ineligible"
    assert by_id["NCT-C"]["eligibility"] == "needs_more_info"
    assert by_id["NCT-C"]["confidence"] == 0.5

    # ranking: eligible first, then needs-info, then ineligible.
    assert [r["nct_id"] for r in results] == ["NCT-A", "NCT-C", "NCT-B"]

    # passthrough fields from the shortlist / route.
    assert by_id["NCT-A"]["url"] == "https://clinicaltrials.gov/study/NCT-A"
    assert by_id["NCT-A"]["similarity"] == 0.91
    assert by_id["NCT-A"]["criteria"][0]["status"] == "met"


def test_match_empty_shortlist_returns_no_results(monkeypatch):
    async def fake_embed(text):
        return [0.0]

    async def fake_shortlist(profile, embedding, match_count=None):
        return []

    monkeypatch.setattr(rm, "embed_text", fake_embed)
    monkeypatch.setattr(rm, "shortlist", fake_shortlist)

    client = TestClient(app)
    resp = client.post("/api/match", json=_PROFILE)
    assert resp.status_code == 200
    assert resp.json() == {"results": []}
