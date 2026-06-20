"""Response models for POST /api/match."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.models.trial import CriterionType

VerdictStatus = Literal["met", "not_met", "unknown"]
Eligibility = Literal["likely_eligible", "needs_more_info", "ineligible"]


class CriterionVerdict(BaseModel):
    """A single criterion plus the model's status + reason."""

    type: CriterionType
    text: str
    status: VerdictStatus
    reason: str


class TrialMatch(BaseModel):
    nct_id: str
    brief_title: str | None
    url: str
    eligibility: Eligibility
    confidence: float
    similarity: float | None = None
    criteria: list[CriterionVerdict]


class MatchResponse(BaseModel):
    results: list[TrialMatch]
