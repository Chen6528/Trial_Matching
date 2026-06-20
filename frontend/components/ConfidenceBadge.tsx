import { formatPercent } from "@/lib/format";

export default function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = formatPercent(confidence);
  return (
    <span
      className="inline-flex items-center gap-2 text-xs text-zinc-500"
      title="Share of criteria with a definite (non-unknown) verdict"
    >
      <span className="font-medium text-zinc-700">{pct}</span>
      <span>confidence</span>
      <span className="h-1.5 w-16 overflow-hidden rounded-full bg-zinc-200">
        <span className="block h-full rounded-full bg-zinc-500" style={{ width: pct }} />
      </span>
    </span>
  );
}
