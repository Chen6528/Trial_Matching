"""POST /api/match — the core endpoint.

Pipeline: profile -> text -> embed -> SQL prefilter + vector rerank (shortlist) ->
parallel per-criterion reasoning -> deterministic aggregation -> ranked results.
"""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter

from app.models.patient import PatientProfile
from app.models.results import MatchResponse, TrialMatch
from app.services import scoring
from app.services.embeddings import embed_text
from app.services.reasoning import evaluate_trial
from app.services.shortlist import shortlist
from app.services.store import load_criteria

router = APIRouter()


@router.post("/match", response_model=MatchResponse)
async def match(profile: PatientProfile) -> MatchResponse:
    patient_text = profile.to_text()
    embedding = await embed_text(patient_text)

    shortlisted = await shortlist(profile, embedding)
    if not shortlisted:
        return MatchResponse(results=[])

    nct_ids = [s["nct_id"] for s in shortlisted]
    criteria_by_nct = await load_criteria(nct_ids)

    async def evaluate(s: dict[str, Any]) -> TrialMatch:
        criteria = criteria_by_nct.get(s["nct_id"], [])
        verdicts = await evaluate_trial(patient_text, criteria)
        eligibility, confidence = scoring.aggregate(verdicts)
        return TrialMatch(
            nct_id=s["nct_id"],
            brief_title=s.get("brief_title"),
            url=f"https://clinicaltrials.gov/study/{s['nct_id']}",
            eligibility=eligibility,
            confidence=confidence,
            similarity=s.get("similarity"),
            criteria=verdicts,
        )

    matches = list(await asyncio.gather(*(evaluate(s) for s in shortlisted)))
    matches.sort(key=scoring.rank_key)
    return MatchResponse(results=matches)
