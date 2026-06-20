# Roadmap & Build Log

Phased build plan for Trial_Matching, mapped to the ~10 hr/week schedule. This is the
in-repo companion to the full design plan (folder structure, schema, prompts, risk
analysis, v1-vs-v2). Status is updated as phases land.

**Status legend:** ✅ done · 🟡 partial / in progress · ⬜ planned

**Snapshot:** Backend matching + ingestion + the eval harness are code-complete and tested.
The Next.js frontend is now built and verified end-to-end against the live local backend
(lint/build/type-check green; a sample match returns ranked trials). Cloud deployment
(Railway + Vercel + Supabase prod) is the remaining piece for v1 — see [`deploy.md`](deploy.md).

---

## Phase 1 — Week 1: Data spine (backend ingest) ✅
**Goal:** recruiting trials in Supabase with normalized criteria + embeddings.

| Piece | Where |
|---|---|
| CT.gov v2 client + age/sex/status parsing | `app/services/clinicaltrials.py` |
| Supabase schema: `trials`, `trial_criteria`, pgvector HNSW index, `match_trials()` RPC | `app/db/schema.sql` |
| Prompt 1 — criteria normalization (Claude **Haiku**) | `app/prompts/extract_criteria.py`, `app/services/extraction.py` |
| OpenAI embeddings (`text-embedding-3-small`) | `app/services/embeddings.py` |
| Persistence (upsert trials + criteria, idempotent) | `app/services/store.py` |
| Ingest pipeline + CLI | `app/services/ingestion.py`, `scripts/ingest.py` |

**Done when:** `python scripts/ingest.py --condition "..."` lands trials in Supabase with embeddings.
**Status:** code-complete; populates the DB once credentials + schema are in place.

## Phase 2 — Week 2: Matching core (backend) ✅
**Goal:** patient profile → ranked trials with per-criterion verdicts + confidence.

| Piece | Where |
|---|---|
| `PatientProfile` + profile→text rendering | `app/models/patient.py` |
| Shortlist: SQL prefilter (status/age/sex) + pgvector rerank via RPC | `app/services/shortlist.py` |
| Prompt 2 — per-criterion reasoning (Claude **Sonnet** + adaptive thinking + prompt caching) | `app/prompts/evaluate_criteria.py`, `app/services/reasoning.py` |
| Deterministic eligibility + confidence aggregation ✅ unit-tested (7/7) | `app/services/scoring.py` |
| `POST /api/match` orchestration (parallel reasoning over the shortlist) | `app/api/routes_match.py` |
| `GET /api/trials/{id}`, `POST /api/ingest`, `GET /api/health` | `app/api/` |

| **Eval harness** — 22-case hand-labeled gold set (negation / threshold / missing-data) + accuracy/confusion/per-tag report, `--model` flag for the Sonnet-vs-Opus gate | `eval/gold_set.jsonl`, `eval/patients.json`, `eval/run_eval.py` |

**Done when:** `/api/match` returns ranked trials with verdicts and `run_eval.py` reports accuracy.
**Status:** code-complete and **run**: Sonnet 4.6 scores 22/22 (100%) on the gold set, and
holds 100% at `reasoning_effort=low` — so Prompt 2 stays on Sonnet at low effort (cheapest),
no Opus escalation needed.

## Phase 3 — Week 3: Frontend + deploy 🟡
**Frontend ✅** — built and verified end-to-end against the local backend.
- Next.js 16 (App Router + TS + Tailwind v4), **single-page** flow in `app/page.tsx`
  (form → loading → results / error) — chosen over a separate results route so the rich
  POST body isn't carried across navigations.
- Components: `IntakeForm`, `TagInput`, `KeyValueInput`, `ResultsList`, `TrialCard`,
  `CriterionRow`, `EligibilityBadge`, `ConfidenceBadge`, `LoadingState`, `DisclaimerBanner`.
- `lib/types.ts` (API contract), `lib/schema.ts` (zod form + transform), `lib/api.ts`
  (direct browser→backend fetch, 120s timeout), `lib/format.ts`. CORS + loading/empty/error states done.

**Deploy ⬜** — Railway (Dockerfile) + Vercel + Supabase prod. Runbook: [`deploy.md`](deploy.md).

**Done when:** a public URL runs the full flow end-to-end.

## Phase 4 — Week 4: Polish / portfolio ⬜
- Tune Prompt 2 against eval failures; add a 3rd condition
- README architecture diagram + demo GIF + design-rationale writeup
- Latency cap; medical disclaimer; basic API tests
- Stretch: SSE streaming of results as each trial resolves

---

## Verified so far
- All backend Python byte-compiles (Python 3.13).
- **7/7 unit tests pass** — eligibility aggregation, result ranking, CT.gov age parsing (`tests/test_scoring.py`).
- **Frontend:** `npm run lint` + `npm run build` (type-check) green.
- **Live end-to-end (local):** `POST /api/match` with the example NSCLC profile returns 15
  ranked trials with per-criterion verdicts + confidence, and CORS allows the frontend
  origin. The LLM / embedding / Supabase paths are now exercised, not just code-complete.
- **Eval ran (gold set):** `eval/run_eval.py` scores Sonnet 4.6 **22/22 (100%)** across
  negation / threshold / missing-data, and **holds 100% at `reasoning_effort=low`** — the
  cheap setting costs no accuracy on the hard cases.

## Key decisions (the "why")
- **Structured prefilter → vector rerank → LLM**, not embedding-only shortlisting — higher precision, lower cost.
- **Tiered models:** Haiku for ingest-time criteria parsing, Sonnet for query-time reasoning; Opus only if eval accuracy falls short.
- **Eligibility is computed deterministically in code**, never by the model — the LLM only judges each criterion's statement (`met`/`not_met`/`unknown`).
- **v1 condition filter is off** (`filter_conditions=None`) — exact array-overlap on free-text condition names is brittle; the small corpus + vector rerank carry relevance. Normalized condition mapping is a v2 item.

## v1 vs v2
**v1** = Phases 1–4 above (2–3 oncology conditions, deterministic confidence, deployed, no auth, ephemeral PHI).
**v2** = per-criterion embeddings (multi-vector retrieval), free-text LLM intake parsing, broader/live ingestion, result caching + Batch API precompute, accounts + saved searches, location filtering, observability, Haiku/Sonnet/Opus A/B with eval metrics.
