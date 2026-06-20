"use client";

import { useState } from "react";

import IntakeForm from "@/components/IntakeForm";
import LoadingState from "@/components/LoadingState";
import ResultsList from "@/components/ResultsList";
import { ApiError, matchTrials } from "@/lib/api";
import type { PatientProfile, TrialMatch } from "@/lib/types";

type Status =
  | { phase: "idle" }
  | { phase: "loading" }
  | { phase: "done"; results: TrialMatch[] }
  | { phase: "error"; message: string };

export default function Home() {
  const [status, setStatus] = useState<Status>({ phase: "idle" });

  async function handleSubmit(profile: PatientProfile) {
    setStatus({ phase: "loading" });
    try {
      const data = await matchTrials(profile);
      setStatus({ phase: "done", results: data.results });
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
      setStatus({ phase: "error", message });
    }
  }

  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-8 sm:py-12">
      <header className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900">
          Clinical Trial Matching
        </h1>
        <p className="mt-1 text-sm text-zinc-600">
          Enter a patient profile to see ClinicalTrials.gov studies ranked by eligibility, each
          with a per-criterion breakdown and a confidence score.
        </p>
      </header>

      <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm sm:p-6">
        <IntakeForm onSubmit={handleSubmit} pending={status.phase === "loading"} />
      </section>

      <section className="mt-8" aria-live="polite">
        {status.phase === "loading" ? <LoadingState /> : null}
        {status.phase === "error" ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            {status.message}
          </div>
        ) : null}
        {status.phase === "done" ? <ResultsList results={status.results} /> : null}
      </section>
    </main>
  );
}
