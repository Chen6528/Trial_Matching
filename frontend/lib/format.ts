/**
 * Shared presentation maps so the badges and rows render eligibility/verdict
 * states consistently. Tailwind class strings live here, keyed by the backend's
 * literal union values.
 */
import type { Eligibility, VerdictStatus } from "@/lib/types";

export const ELIGIBILITY_META: Record<
  Eligibility,
  { label: string; badge: string; dot: string }
> = {
  likely_eligible: {
    label: "Likely eligible",
    badge: "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/20",
    dot: "bg-emerald-500",
  },
  needs_more_info: {
    label: "Needs more info",
    badge: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-600/20",
    dot: "bg-amber-500",
  },
  ineligible: {
    label: "Ineligible",
    badge: "bg-rose-50 text-rose-700 ring-1 ring-inset ring-rose-600/20",
    dot: "bg-rose-500",
  },
};

export const STATUS_META: Record<
  VerdictStatus,
  { label: string; symbol: string; className: string }
> = {
  met: { label: "Met", symbol: "✓", className: "text-emerald-600" },
  not_met: { label: "Not met", symbol: "✗", className: "text-rose-600" },
  unknown: { label: "Unknown", symbol: "?", className: "text-zinc-400" },
};

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}
