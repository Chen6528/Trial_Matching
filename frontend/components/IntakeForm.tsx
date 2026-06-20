"use client";

import type { ReactNode } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import KeyValueInput from "@/components/KeyValueInput";
import TagInput from "@/components/TagInput";
import {
  ECOG_OPTIONS,
  EMPTY_FORM,
  EXAMPLE_FORM,
  SEX_OPTIONS,
  patientFormSchema,
  toPatientProfile,
  type PatientFormValues,
} from "@/lib/schema";
import type { PatientProfile } from "@/lib/types";

interface IntakeFormProps {
  onSubmit: (profile: PatientProfile) => void;
  pending: boolean;
}

// A few ingested conditions to surface as autocomplete hints.
const CONDITION_SUGGESTIONS = [
  "non-small cell lung cancer",
  "breast cancer",
  "melanoma",
];

const inputClass =
  "w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-200";

function Field({
  label,
  htmlFor,
  hint,
  error,
  children,
}: {
  label: string;
  htmlFor?: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="block text-sm font-medium text-zinc-800">
        {label}
      </label>
      {children}
      {hint && !error ? <p className="text-xs text-zinc-500">{hint}</p> : null}
      {error ? <p className="text-xs text-rose-600">{error}</p> : null}
    </div>
  );
}

export default function IntakeForm({ onSubmit, pending }: IntakeFormProps) {
  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PatientFormValues>({
    resolver: zodResolver(patientFormSchema),
    defaultValues: EMPTY_FORM,
  });

  const submit = handleSubmit((values) => onSubmit(toPatientProfile(values)));

  return (
    <form onSubmit={submit} className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-zinc-900">Patient profile</h2>
        <div className="flex gap-3 text-sm">
          <button
            type="button"
            onClick={() => reset(EXAMPLE_FORM)}
            className="font-medium text-zinc-600 hover:text-zinc-900"
          >
            Prefill example
          </button>
          <button
            type="button"
            onClick={() => reset(EMPTY_FORM)}
            className="font-medium text-zinc-400 hover:text-zinc-700"
          >
            Clear
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Age" htmlFor="age" error={errors.age?.message}>
          <input
            id="age"
            type="number"
            min={0}
            max={120}
            inputMode="numeric"
            placeholder="e.g. 62"
            className={inputClass}
            {...register("age")}
          />
        </Field>

        <Field label="Sex" htmlFor="sex" error={errors.sex?.message}>
          <select id="sex" className={inputClass} {...register("sex")}>
            {SEX_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </Field>
      </div>

      <Field
        label="Primary condition"
        htmlFor="condition"
        error={errors.condition?.message}
      >
        <input
          id="condition"
          list="condition-suggestions"
          placeholder="e.g. non-small cell lung cancer"
          className={inputClass}
          {...register("condition")}
        />
        <datalist id="condition-suggestions">
          {CONDITION_SUGGESTIONS.map((c) => (
            <option key={c} value={c} />
          ))}
        </datalist>
      </Field>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Stage" htmlFor="stage" hint="Optional">
          <input
            id="stage"
            placeholder="e.g. IV or metastatic"
            className={inputClass}
            {...register("stage")}
          />
        </Field>

        <Field label="ECOG performance status" htmlFor="ecog_status" hint="Optional">
          <select id="ecog_status" className={inputClass} {...register("ecog_status")}>
            <option value="">Unknown</option>
            {ECOG_OPTIONS.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        </Field>
      </div>

      <Field label="Biomarkers" htmlFor="biomarkers" hint="Press Enter to add each one">
        <Controller
          control={control}
          name="biomarkers"
          render={({ field }) => (
            <TagInput
              id="biomarkers"
              value={field.value}
              onChange={field.onChange}
              placeholder="e.g. EGFR exon 19 deletion"
            />
          )}
        />
      </Field>

      <Field
        label="Prior treatments"
        htmlFor="prior_treatments"
        hint="Press Enter to add each one"
      >
        <Controller
          control={control}
          name="prior_treatments"
          render={({ field }) => (
            <TagInput
              id="prior_treatments"
              value={field.value}
              onChange={field.onChange}
              placeholder="e.g. osimertinib"
            />
          )}
        />
      </Field>

      <Field label="Comorbidities" htmlFor="comorbidities" hint="Press Enter to add each one">
        <Controller
          control={control}
          name="comorbidities"
          render={({ field }) => (
            <TagInput
              id="comorbidities"
              value={field.value}
              onChange={field.onChange}
              placeholder="e.g. hypertension"
            />
          )}
        />
      </Field>

      <Field label="Lab values" hint="Optional">
        <Controller
          control={control}
          name="lab_values"
          render={({ field }) => (
            <KeyValueInput value={field.value} onChange={field.onChange} />
          )}
        />
      </Field>

      <Field label="Additional notes" htmlFor="additional_notes" hint="Optional">
        <textarea
          id="additional_notes"
          rows={3}
          placeholder="Anything not captured above"
          className={inputClass}
          {...register("additional_notes")}
        />
      </Field>

      <button
        type="submit"
        disabled={pending}
        className="w-full rounded-md bg-zinc-900 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-zinc-700 disabled:cursor-not-allowed disabled:bg-zinc-400"
      >
        {pending ? "Matching trials…" : "Find matching trials"}
      </button>
    </form>
  );
}
