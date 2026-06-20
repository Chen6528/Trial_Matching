/**
 * TypeScript mirrors of the backend Pydantic models.
 *
 * Request shape mirrors `app/models/patient.py` (PatientProfile); response shapes
 * mirror `app/models/results.py` (MatchResponse / TrialMatch / CriterionVerdict).
 * Keep these in sync with the backend — they are the API contract.
 */

// --- Request (POST /api/match body) ---

export type Sex = "MALE" | "FEMALE";

export interface PatientProfile {
  age: number;
  sex: Sex;
  condition: string;
  stage: string | null;
  biomarkers: string[];
  prior_treatments: string[];
  ecog_status: number | null;
  comorbidities: string[];
  lab_values: Record<string, string>;
  additional_notes: string | null;
}

// --- Response (POST /api/match) ---

export type CriterionType = "inclusion" | "exclusion";
export type VerdictStatus = "met" | "not_met" | "unknown";
export type Eligibility = "likely_eligible" | "needs_more_info" | "ineligible";

export interface CriterionVerdict {
  type: CriterionType;
  text: string;
  status: VerdictStatus;
  reason: string;
}

export interface TrialMatch {
  nct_id: string;
  brief_title: string | null;
  url: string;
  eligibility: Eligibility;
  confidence: number;
  similarity: number | null;
  criteria: CriterionVerdict[];
}

export interface MatchResponse {
  results: TrialMatch[];
}
