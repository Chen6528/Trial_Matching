# Trial_Matching

Full-stack clinical trial matching: a patient/clinician fills out an intake form and gets a
**ranked list of ClinicalTrials.gov trials they're plausibly eligible for**, each with a
**per-criterion eligibility breakdown** and a **confidence score**.

The differentiator is correctness on eligibility *logic* — negations ("no prior EGFR TKI"),
numeric thresholds ("eGFR ≥ 60"), and age/sex windows — which embedding similarity alone
cannot resolve. So matching is a two-stage pipeline:

1. **Retrieve & shortlist** — pull recruiting trials from the CT.gov v2 API, normalize their
   criteria (Claude Haiku) and embed them (OpenAI) into Supabase/pgvector. At query time:
   structured SQL prefilter (status + age/sex) **then** vector cosine rerank → ~15 candidates.
2. **Reason per-criterion** — for each candidate, Claude Sonnet judges every criterion
   (`met` / `not_met` / `unknown`) with a cited reason; eligibility + confidence are then
   computed **deterministically in code**, never by the model.

## Architecture
```
Next.js intake form ──> FastAPI /api/match ──> OpenAI embed
                                          └──> Supabase pgvector (prefilter + rerank)
                                          └──> Claude Sonnet (per-criterion reasoning)
                                          └──> deterministic scoring ──> ranked results
ingest: CT.gov v2 ──> Claude Haiku (normalize criteria) ──> OpenAI embed ──> Supabase
```

## Repo
- [`backend/`](backend/) — FastAPI service (matching, ingestion, Supabase schema). **Built.** See its [README](backend/README.md).
- [`frontend/`](frontend/) — Next.js intake form + results UI. **Built.** See its [README](frontend/README.md).

Stack: FastAPI · Supabase/pgvector · OpenAI `text-embedding-3-small` · Claude (Haiku ingest,
Sonnet reasoning) · Next.js · deploys to Railway + Vercel (see [`docs/deploy.md`](docs/deploy.md)).

See [`docs/roadmap.md`](docs/roadmap.md) for the phased build plan (week-by-week status,
what's built, key decisions, and v1-vs-v2).

> **Disclaimer:** decision-support tool, not medical advice. No patient data is persisted.
