# Roadmap & Build Log

Phased build plan for Trial_Matching, mapped to the ~10 hr/week schedule. This is the
in-repo companion to the full design plan (folder structure, schema, prompts, risk
analysis, v1-vs-v2). Status is updated as phases land.

**Status legend:** ✅ done · 🟡 partial / in progress · ⬜ planned

**Snapshot:** Backend matching + ingestion pipeline and the eval harness are code-complete
and unit-/structurally-tested. They need credentials (Anthropic + OpenAI + Supabase) and the
schema applied to run end-to-end. The frontend is the remaining piece for v1.

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
**Status:** code-complete; gold set structurally validated. Running it for real numbers needs
`ANTHROPIC_API_KEY` (`python eval/run_eval.py`) — this is the gate for confirming Sonnet vs
escalating Prompt 2 to Opus.

## Phase 3 — Week 3: Frontend + deploy ⬜
- Next.js (App Router + TS + Tailwind): intake form (`app/page.tsx`) + results page (`app/results/page.tsx`)
- Components: `IntakeForm`, `TrialCard`, `CriterionRow`, `ConfidenceBadge`, `EligibilityBadge`
- Wire to backend (`lib/api.ts`, `lib/types.ts`); CORS; loading/error states
- Deploy: Railway (Dockerfile) + Vercel + Supabase prod

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
- LLM / embedding / Supabase paths are code-complete but **unrun** (need credentials).

## Key decisions (the "why")
- **Structured prefilter → vector rerank → LLM**, not embedding-only shortlisting — higher precision, lower cost.
- **Tiered models:** Haiku for ingest-time criteria parsing, Sonnet for query-time reasoning; Opus only if eval accuracy falls short.
- **Eligibility is computed deterministically in code**, never by the model — the LLM only judges each criterion's statement (`met`/`not_met`/`unknown`).
- **v1 condition filter is off** (`filter_conditions=None`) — exact array-overlap on free-text condition names is brittle; the small corpus + vector rerank carry relevance. Normalized condition mapping is a v2 item.

## v1 vs v2
**v1** = Phases 1–4 above (2–3 oncology conditions, deterministic confidence, deployed, no auth, ephemeral PHI).
**v2** = per-criterion embeddings (multi-vector retrieval), free-text LLM intake parsing, broader/live ingestion, result caching + Batch API precompute, accounts + saved searches, location filtering, observability, Haiku/Sonnet/Opus A/B with eval metrics.
