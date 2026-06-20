# Frontend — Clinical Trial Matching

Next.js (App Router) intake form + results UI for the matching API. A single page
collects a patient profile, POSTs it to the backend's `/api/match`, and renders the
ranked trials with a per-criterion eligibility breakdown and a confidence score.

Stack: Next.js 16 · React 19 · TypeScript · Tailwind v4 · react-hook-form + zod.

## Run locally

Start the backend first (see [`../backend`](../backend)) — by default at
`http://localhost:8000`. Then:

```bash
npm install
# copy .env.example to .env.local (defaults to the backend on :8000)
npm run dev          # http://localhost:3000
```

Click **Prefill example** to load a sample NSCLC case, then **Find matching trials**.

## Scripts
- `npm run dev` — dev server (Turbopack)
- `npm run build` — production build (also type-checks)
- `npm run lint` — ESLint

## Structure
- `app/page.tsx` — single-page flow (form → loading → results / error)
- `app/layout.tsx` — root layout, fonts, disclaimer banner
- `components/` — `IntakeForm`, `TagInput`, `KeyValueInput`, `ResultsList`, `TrialCard`,
  `CriterionRow`, `EligibilityBadge`, `ConfidenceBadge`, `LoadingState`, `DisclaimerBanner`
- `lib/types.ts` — TS mirrors of the backend Pydantic models (the API contract)
- `lib/schema.ts` — zod form schema + `toPatientProfile` transform
- `lib/api.ts` — `matchTrials()` client (direct browser→backend fetch, 120s timeout)
- `lib/format.ts` — eligibility / verdict label + color maps

## Notes
- The browser calls the backend **directly** via `NEXT_PUBLIC_API_URL` (not a Next.js
  route handler): `/api/match` can take tens of seconds, which would exceed a serverless
  function timeout. The backend allows this origin via `CORS_ORIGINS`.
- Deployment: see [`../docs/deploy.md`](../docs/deploy.md).

> Decision-support demo, not medical advice. No patient data is stored.
