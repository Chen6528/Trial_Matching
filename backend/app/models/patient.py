"""Patient intake profile — the input to POST /api/match.

`to_text()` renders the structured form into a single natural-language paragraph
that is (a) embedded for the vector rerank and (b) handed to the reasoning prompt.
Keeping one canonical rendering means the embedded text and the reasoned-over text
never drift apart.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Sex = Literal["MALE", "FEMALE"]


class PatientProfile(BaseModel):
    age: int = Field(ge=0, le=120, description="Age in years.")
    sex: Sex
    condition: str = Field(description="Primary diagnosis, e.g. 'non-small cell lung cancer'.")
    stage: str | None = Field(default=None, description="Disease stage, e.g. 'IV' or 'metastatic'.")
    biomarkers: list[str] = Field(
        default_factory=list, description="e.g. ['EGFR positive', 'PD-L1 50%']."
    )
    prior_treatments: list[str] = Field(
        default_factory=list, description="e.g. ['platinum chemotherapy', 'osimertinib']."
    )
    ecog_status: int | None = Field(
        default=None, ge=0, le=5, description="ECOG performance status, 0-4."
    )
    comorbidities: list[str] = Field(default_factory=list)
    lab_values: dict[str, str] = Field(
        default_factory=dict, description="e.g. {'eGFR': '72 mL/min', 'ANC': '2.1'}."
    )
    additional_notes: str | None = Field(
        default=None, description="Anything not captured by the structured fields."
    )

    def to_text(self) -> str:
        parts: list[str] = []
        stage = f" stage {self.stage}" if self.stage else ""
        parts.append(
            f"{self.age}-year-old {self.sex.lower()} patient with{stage} {self.condition}."
        )
        if self.biomarkers:
            parts.append("Biomarkers: " + ", ".join(self.biomarkers) + ".")
        if self.prior_treatments:
            parts.append("Prior treatments: " + ", ".join(self.prior_treatments) + ".")
        else:
            parts.append("No prior treatments reported.")
        if self.ecog_status is not None:
            parts.append(f"ECOG performance status {self.ecog_status}.")
        if self.comorbidities:
            parts.append("Comorbidities: " + ", ".join(self.comorbidities) + ".")
        if self.lab_values:
            labs = ", ".join(f"{k} {v}" for k, v in self.lab_values.items())
            parts.append("Labs: " + labs + ".")
        if self.additional_notes:
            parts.append(self.additional_notes.strip())
        return " ".join(parts)
