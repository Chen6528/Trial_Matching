import TrialCard from "@/components/TrialCard";
import type { TrialMatch } from "@/lib/types";

export default function ResultsList({ results }: { results: TrialMatch[] }) {
  if (results.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-zinc-300 bg-white p-8 text-center">
        <p className="text-sm font-medium text-zinc-700">No matching trials found</p>
        <p className="mt-1 text-sm text-zinc-500">
          Try a broader condition or remove some constraints.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-zinc-500">
        {results.length} {results.length === 1 ? "trial" : "trials"} ranked by eligibility, then
        confidence.
      </p>
      {results.map((trial) => (
        <TrialCard key={trial.nct_id} trial={trial} />
      ))}
    </div>
  );
}
