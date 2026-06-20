import { STATUS_META } from "@/lib/format";
import type { CriterionVerdict } from "@/lib/types";

export default function CriterionRow({ verdict }: { verdict: CriterionVerdict }) {
  const meta = STATUS_META[verdict.status];
  return (
    <li className="flex gap-3 py-2.5">
      <span
        className={`mt-0.5 w-4 shrink-0 select-none text-center text-sm font-bold ${meta.className}`}
        aria-label={meta.label}
      >
        {meta.symbol}
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-zinc-800">{verdict.text}</span>
          <span className="rounded bg-zinc-100 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-zinc-500">
            {verdict.type}
          </span>
        </div>
        <p className="mt-0.5 text-xs text-zinc-500">{verdict.reason}</p>
      </div>
    </li>
  );
}
