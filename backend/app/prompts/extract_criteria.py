"""Prompt 1 — criteria extraction / normalization (runs at ingest time, on Haiku).

Turns the messy free-text `eligibilityCriteria` blob into a list of atomic, typed
criteria. Used with `messages.parse(output_format=ParsedCriteria)`.
"""
from __future__ import annotations

from pydantic import BaseModel

from app.models.trial import CriterionCategory, CriterionType

SYSTEM = """\
You normalize ClinicalTrials.gov eligibility text into a list of atomic, \
self-contained criteria. Output ONLY data matching the provided schema.

Rules:
- Split compound bullets into separate atomic criteria (one requirement each).
- Preserve numeric thresholds, units, and comparison operators EXACTLY \
(e.g. "eGFR >= 60 mL/min").
- Preserve negations EXACTLY ("no prior", "without", "absence of").
- Set "type" to "inclusion" or "exclusion". If the source text does not label a \
section, infer from wording (exclusionary phrasing -> exclusion).
- Tag "category": demographics | condition | biomarker | prior_treatment | lab | \
comorbidity | performance_status | other.
- Drop pure administrative/consent boilerplate (e.g. "able to provide informed consent").
- Do NOT invent criteria that are not present in the source text.\
"""


class ExtractedCriterion(BaseModel):
    type: CriterionType
    category: CriterionCategory
    text: str


class ParsedCriteria(BaseModel):
    criteria: list[ExtractedCriterion]


def build_user_message(raw_criteria: str) -> str:
    return f"Eligibility criteria text:\n\n{raw_criteria.strip()}"
