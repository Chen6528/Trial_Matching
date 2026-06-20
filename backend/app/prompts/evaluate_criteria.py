"""Prompt 2 — per-criterion eligibility reasoning (runs per query, on Sonnet).

For each criterion the model returns whether the *statement* is true of the patient
(met / not_met / unknown) plus a one-sentence reason. Overall trial eligibility is
computed deterministically downstream in `services/scoring.py` — the model never
decides eligibility itself.

The SYSTEM block is stable across every trial in a single /match request, so it is
sent with `cache_control: ephemeral` to share a cached prefix across the parallel calls.
"""
from __future__ import annotations

from pydantic import BaseModel

from app.models.results import VerdictStatus
from app.models.trial import Criterion

SYSTEM = """\
You evaluate whether a patient meets each clinical-trial eligibility criterion, using \
ONLY the patient profile provided. For each criterion return:
  - status: "met" | "not_met" | "unknown"
      met     = the criterion STATEMENT is TRUE of this patient
      not_met = the statement is FALSE of this patient
      unknown = the profile does not contain the information needed to decide
  - reason: one sentence citing the specific patient fact and the criterion. Quote the \
relevant patient value. Never speculate beyond the profile.

Critical rules:
- If the needed fact is absent from the profile, you MUST answer "unknown" -- never guess.
- Evaluate the literal logic, including negations and numeric thresholds. "No prior X" is \
met only if the patient has NOT had X. "eGFR >= 60" is met only if the value is >= 60.
- Judge each criterion's STATEMENT independently; do NOT decide overall trial eligibility \
(that is computed downstream). An exclusion criterion being "met" is expected and fine.
- Return exactly one evaluation per input criterion, echoing its criterion_id.

Examples:
- (exclusion) "Prior treatment with an EGFR TKI" | patient: "received osimertinib in 2023"
  -> met  (statement is true; downstream this disqualifies)
- (inclusion) "eGFR >= 60 mL/min" | patient: "eGFR 45" -> not_met
- (inclusion) "ECOG performance status 0-1" | patient: no ECOG mentioned -> unknown
- (exclusion) "Active brain metastases" | patient: "no CNS involvement" -> not_met\
"""


class CriterionEvaluation(BaseModel):
    criterion_id: int
    status: VerdictStatus
    reason: str


class CriterionEvaluations(BaseModel):
    evaluations: list[CriterionEvaluation]


def build_user_message(patient_text: str, criteria: list[Criterion]) -> str:
    lines = [f"{i} | {c.type} | {c.text}" for i, c in enumerate(criteria, start=1)]
    criteria_block = "\n".join(lines)
    return (
        f"PATIENT PROFILE:\n{patient_text}\n\n"
        f"CRITERIA (criterion_id | type | text):\n{criteria_block}"
    )
