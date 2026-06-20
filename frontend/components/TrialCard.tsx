"use client";

import { useState } from "react";

import ConfidenceBadge from "@/components/ConfidenceBadge";
import CriterionRow from "@/components/CriterionRow";
import EligibilityBadge from "@/components/EligibilityBadge";
import type { TrialMatch } from "@/lib/types";

export default function TrialCard({ trial }: { trial: TrialMatch }) {
  const [open, setOpen] = useState(false);

  const counts = { met: 0, not_met: 0, unknown: 0 };
  for (const c of trial.criteria) counts[c.status] += 1;
  const total = trial.criteria.length;

  return (
    <article className="rounded-lg border border-zinc-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-medium text-zinc-900">{trial.brief_title ?? trial.nct_id}</h3>
          <a
            href={trial.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-zinc-500 hover:text-zinc-800 hover:underline"
          >
            {trial.nct_id} ↗
          </a>
        </div>
        <EligibilityBadge eligibility={trial.eligibility} />
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1">
        <ConfidenceBadge confidence={trial.confidence} />
        {trial.similarity !== null ? (
          <span className="text-xs text-zinc-400">similarity {trial.similarity.toFixed(2)}</span>
        ) : null}
      </div>

      {total > 0 ? (
        <>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            className="mt-3 text-sm font-medium text-zinc-600 hover:text-zinc-900"
          >
            {open ? "Hide" : "Show"} {total} criteria
            <span className="ml-2 text-xs font-normal text-zinc-400">
              {counts.met} met · {counts.not_met} not met · {counts.unknown} unknown
            </span>
          </button>

          {open ? (
            <ul className="mt-1 divide-y divide-zinc-100 border-t border-zinc-100">
              {trial.criteria.map((verdict, i) => (
                <CriterionRow key={i} verdict={verdict} />
              ))}
            </ul>
          ) : null}
        </>
      ) : null}
    </article>
  );
}
