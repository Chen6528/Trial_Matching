# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Clinical trial matching app: a patient/clinician intake form returns a ranked list of
ClinicalTrials.gov trials with a per-criterion eligibility breakdown and a confidence score.
Monorepo — `backend/` (FastAPI) and `frontend/` (Next.js 16, App Router) are both built and
verified end-to-end. Cloud deploy is **intentionally out of scope** (personal project); the whole
stack runs locally with `docker compose up`. Phased status and rationale live in `docs/roadmap.md`;
`docs/deploy.md` is an optional hosting appendix.

**Frontend work has its own rules:** `frontend/AGENTS.md` flags that this is Next.js 16 with
breaking changes from older versions — read the relevant guide in `frontend/node_modules/next/dist/docs/`
before writing frontend code.

## Commands (run from `backend/`)

```bash
python -m venv .venv && .venv\Scripts\activate   # macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"                          # editable install — `app` importable everywhere
cp .env.example .env                             # fill Anthropic + OpenAI + Supabase keys

uvicorn app.main:app --reload                    # API + Swagger at /docs
pytest                                           # unit tests
pytest tests/test_scoring.py::test_parse_age     # a single test
ruff check .                                     # lint

python scripts/ingest.py --condition "non-small cell lung cancer" --max 200   # populate the DB
python eval/run_eval.py                          # per-criterion reasoning accuracy (needs ANTHROPIC_API_KEY)
python eval/run_eval.py --model claude-opus-4-8  # Sonnet-vs-Opus gate on the gold set
```

The Supabase schema is **not** auto-applied: run `app/db/schema.sql` once in the Supabase SQL
editor (creates `trials`, `trial_criteria`, the pgvector HNSW index, and the `match_trials` RPC).

## Commands (run from `frontend/`)

```bash
npm install
npm run dev      # Next dev server at http://localhost:3000 (expects backend at :8000)
npm run build    # production build + type-check
npm run lint     # eslint
npm run test     # Vitest + React Testing Library (jsdom)
```

The browser fetches the FastAPI backend **directly** (`lib/api.ts`); set `NEXT_PUBLIC_API_URL`
to point at a non-local backend (defaults to `http://localhost:8000`). Or run both together from
the repo root: `docker compose up --build` (backend on :8000, frontend on :3000).

## Architecture — two pipelines, one trust boundary

**Ingest (offline):** `scripts/ingest.py` → `services/ingestion.py`: CT.gov v2 fetch →
**Prompt 1 / Haiku** normalizes the messy free-text `eligibilityCriteria` into atomic typed
criteria → OpenAI embed → upsert to Supabase (`trials` + `trial_criteria`).

**Query (`POST /api/match`, `api/routes_match.py`):** `PatientProfile.to_text()` → embed →
`match_trials` RPC (SQL prefilter on status/age/sex **then** pgvector cosine rerank → ~15
candidates) → **Prompt 2 / Sonnet** judges each criterion in parallel → `services/scoring.py`
aggregates → ranked results.

**Frontend:** single-page flow in `app/page.tsx` (form → loading → results / error). The
browser POSTs `PatientProfile` straight to the backend's `/api/match` (no Next route handler)
because the per-trial reasoning fan-out can take tens of seconds — past a serverless timeout but
fine for a direct request with a 120s client cap. `lib/types.ts` mirrors the API contract;
`lib/schema.ts` is the zod form + transform.

**The trust boundary (most important):** the LLM in `services/reasoning.py` only labels each
criterion `met` / `not_met` / `unknown`. Overall eligibility and confidence are computed
**deterministically** in `services/scoring.py` — never move the eligible/ineligible decision
into the prompt. That separation is the core correctness design.

## Invariants to preserve

- **Two model tiers come from settings** (`config.py`): `extraction_model` (Haiku, ingest) and
  `reasoning_model` (Sonnet, query). Don't hardcode model IDs in services. Prompt 2's thinking
  spend is controlled by `reasoning_effort` (default `"low"`, the supported lever on Sonnet 4.6 —
  `budget_tokens` is deprecated); the eval gate holds 100% at low, so raise it only if eval slips.
- **Structured outputs** use `client.messages.parse(output_format=PydanticModel)` → `.parsed_output`.
  Each prompt's output schema lives beside its text in `app/prompts/`.
- **One canonical patient rendering:** `PatientProfile.to_text()` feeds *both* the embedding and
  the reasoning prompt. Keep it unified — don't add a second rendering that can drift.
- **Criterion id mapping:** `reasoning.py` sends criteria 1-indexed and maps results back by
  `criterion_id`; a missing id defaults to `unknown`. Preserve this 1:1 mapping.
- **Supabase client is synchronous** — wrap every call in `asyncio.to_thread` inside async code
  (see `services/shortlist.py`, `services/store.py`).
- **`filter_conditions` is passed `None` in v1 on purpose** (`services/shortlist.py`): exact
  array-overlap on free-text condition names is brittle. Don't "fix" it by enabling exact match;
  normalized condition mapping is a v2 item.
- **Prompt 2's system block uses `cache_control: ephemeral`** so the parallel per-trial calls in
  one request share a cached prefix — keep the system text stable and first.

## Status & scope

Backend matching + ingestion, the eval harness (`eval/`), and the Next.js frontend are all built
and verified end-to-end (12/12 backend tests incl. a mocked `/api/match` integration test; 3
frontend Vitest tests; `ruff` / `lint` / `build` green). CI runs all of this on push
(`.github/workflows/ci.yml`); `docker compose up` runs the full stack locally. Eval: Sonnet 4.6
scored **22/22** at `reasoning_effort=low` on the original 22-case set; the gold set is now **65**
cases — re-run `eval/run_eval.py` (needs a key) to score it. **Cloud deploy is out of scope**
(personal project; `docs/deploy.md` is an optional appendix). Next work is the Tier 3 backlog in
`docs/roadmap.md` (free-text intake, SSE streaming, per-criterion embeddings, cost logging).
Decision-support tool only, not medical advice; patient input is not persisted.
