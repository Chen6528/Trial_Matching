/**
 * Intake-form schema + transform to the API payload.
 *
 * The form holds UI-friendly values (numbers as strings, lab values as
 * {key,value} rows). `toPatientProfile` converts that into the `PatientProfile`
 * shape the backend expects. Validation lives in zod; transforms are kept out of
 * the schema so the resolved form type stays simple for react-hook-form.
 */
import { z } from "zod";

import type { PatientProfile, Sex } from "@/lib/types";

export const SEX_OPTIONS: { value: Sex; label: string }[] = [
  { value: "MALE", label: "Male" },
  { value: "FEMALE", label: "Female" },
];

// ECOG performance status. Standard scale is 0–4; the backend accepts 0–5.
export const ECOG_OPTIONS = ["0", "1", "2", "3", "4"] as const;

const labRowSchema = z.object({
  key: z.string(),
  value: z.string(),
});

export const patientFormSchema = z.object({
  age: z
    .string()
    .min(1, "Age is required")
    .refine((v) => {
      const n = Number(v);
      return Number.isInteger(n) && n >= 0 && n <= 120;
    }, "Enter a whole number between 0 and 120"),
  sex: z.enum(["MALE", "FEMALE"]),
  condition: z.string().trim().min(1, "Primary condition is required"),
  stage: z.string(),
  ecog_status: z.string(), // "" = unknown, otherwise "0".."4"
  biomarkers: z.array(z.string()),
  prior_treatments: z.array(z.string()),
  comorbidities: z.array(z.string()),
  lab_values: z.array(labRowSchema),
  additional_notes: z.string(),
});

export type PatientFormValues = z.infer<typeof patientFormSchema>;

export const EMPTY_FORM: PatientFormValues = {
  age: "",
  sex: "MALE",
  condition: "",
  stage: "",
  ecog_status: "",
  biomarkers: [],
  prior_treatments: [],
  comorbidities: [],
  lab_values: [],
  additional_notes: "",
};

// A realistic NSCLC case for the "Prefill example" button (uses an ingested
// condition so the vector rerank returns relevant trials).
export const EXAMPLE_FORM: PatientFormValues = {
  age: "62",
  sex: "FEMALE",
  condition: "non-small cell lung cancer",
  stage: "IV",
  ecog_status: "1",
  biomarkers: ["EGFR exon 19 deletion", "PD-L1 30%"],
  prior_treatments: ["osimertinib", "platinum-based chemotherapy"],
  comorbidities: ["hypertension"],
  lab_values: [
    { key: "eGFR", value: "78 mL/min" },
    { key: "ANC", value: "2.4 x10^9/L" },
  ],
  additional_notes: "Disease progression after first-line osimertinib.",
};

function cleanList(items: string[]): string[] {
  return items.map((s) => s.trim()).filter((s) => s.length > 0);
}

export function toPatientProfile(values: PatientFormValues): PatientProfile {
  const lab_values: Record<string, string> = {};
  for (const { key, value } of values.lab_values) {
    const k = key.trim();
    const v = value.trim();
    if (k && v) lab_values[k] = v;
  }

  const stage = values.stage.trim();
  const notes = values.additional_notes.trim();

  return {
    age: Number(values.age),
    sex: values.sex,
    condition: values.condition.trim(),
    stage: stage || null,
    biomarkers: cleanList(values.biomarkers),
    prior_treatments: cleanList(values.prior_treatments),
    ecog_status: values.ecog_status === "" ? null : Number(values.ecog_status),
    comorbidities: cleanList(values.comorbidities),
    lab_values,
    additional_notes: notes || null,
  };
}
