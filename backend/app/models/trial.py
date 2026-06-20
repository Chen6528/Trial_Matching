"""Trial + parsed-criterion domain models (stored in Supabase, returned by /api/trials)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

CriterionType = Literal["inclusion", "exclusion"]
CriterionCategory = Literal[
    "demographics",
    "condition",
    "biomarker",
    "prior_treatment",
    "lab",
    "comorbidity",
    "performance_status",
    "other",
]


class Criterion(BaseModel):
    """One atomic eligibility criterion (output of the extraction pass)."""

    type: CriterionType
    category: CriterionCategory
    text: str


class Trial(BaseModel):
    """Trial metadata as stored/returned. Embedding + raw_json omitted from the API view."""

    nct_id: str
    brief_title: str | None = None
    conditions: list[str] = []
    overall_status: str | None = None
    sex: str | None = None
    min_age_years: float | None = None
    max_age_years: float | None = None
    healthy_volunteers: bool | None = None
    eligibility_criteria: str | None = None
    criteria: list[Criterion] = []

    @property
    def url(self) -> str:
        return f"https://clinicaltrials.gov/study/{self.nct_id}"
