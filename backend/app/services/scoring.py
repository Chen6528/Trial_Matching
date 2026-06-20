"""Deterministic eligibility + confidence aggregation.

This is the trust boundary: the LLM judges each criterion's *statement*, but the
final eligible/ineligible decision and confidence are computed here, in plain code,
from the criterion type + status. No model call decides eligibility.
"""
from __future__ import annotations

from app.models.results import CriterionVerdict, Eligibility, TrialMatch

# Result ordering: eligible first, then needs-info, then ineligible.
_BUCKET_ORDER: dict[Eligibility, int] = {
    "likely_eligible": 0,
    "needs_more_info": 1,
    "ineligible": 2,
}


def _is_disqualifying(v: CriterionVerdict) -> bool:
    # An inclusion the patient fails, or an exclusion the patient matches.
    return (v.type == "inclusion" and v.status == "not_met") or (
        v.type == "exclusion" and v.status == "met"
    )


def aggregate(verdicts: list[CriterionVerdict]) -> tuple[Eligibility, float]:
    """Roll per-criterion verdicts up into (eligibility, confidence).

    - any disqualifying criterion          -> ineligible
    - else any unknown (missing patient data) -> needs_more_info
    - else                                  -> likely_eligible
    confidence = share of criteria with a definite (non-unknown) verdict.
    """
    if not verdicts:
        return "needs_more_info", 0.0

    unknown = sum(1 for v in verdicts if v.status == "unknown")
    confidence = round(1 - unknown / len(verdicts), 2)

    if any(_is_disqualifying(v) for v in verdicts):
        return "ineligible", confidence
    if unknown:
        return "needs_more_info", confidence
    return "likely_eligible", confidence


def rank_key(match: TrialMatch) -> tuple[int, float]:
    """Sort key for the results list: bucket asc, then confidence desc."""
    return (_BUCKET_ORDER[match.eligibility], -match.confidence)
