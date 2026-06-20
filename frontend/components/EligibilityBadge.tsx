import { ELIGIBILITY_META } from "@/lib/format";
import type { Eligibility } from "@/lib/types";

export default function EligibilityBadge({ eligibility }: { eligibility: Eligibility }) {
  const meta = ELIGIBILITY_META[eligibility];
  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${meta.badge}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />
      {meta.label}
    </span>
  );
}
