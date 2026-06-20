# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Clinical trial matching app: a patient/clinician intake form returns a ranked list of
ClinicalTrials.gov trials with a per-criterion eligibility breakdown and a confidence score.
Monorepo — `backend/` (FastAPI, built) and `frontend/` (Next.js, planned). Phased status and
rationale live in `docs/roadmap.md`.

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
```

The Supabase schema is **not** auto-applied: run `app/db/schema.sql` once in the Supabase SQL
editor (creates `trials`, `trial_criteria`, the pgvector HNSW index, and the `match_trials` RPC).

## Architecture — two pipelines, one trust boundary

**Ingest (offline):** `scripts/ingest.py` → `services/ingestion.py`: CT.gov v2 fetch →
**Prompt 1 / Haiku** normalizes the messy free-text `eligibilityCriteria` into atomic typed
criteria → OpenAI embed → upsert to Supabase (`trials` + `trial_criteria`).

**Query (`POST /api/match`, `api/routes_match.py`):** `PatientProfile.to_text()` → embed →
`match_trials` RPC (SQL prefilter on status/age/sex **then** pgvector cosine rerank → ~15
candidates) → **Prompt 2 / Sonnet** judges each criterion in parallel → `services/scoring.py`
aggregates → ranked results.

**The trust boundary (most important):** the LLM in `services/reasoning.py` only labels each
criterion `met` / `not_met` / `unknown`. Overall eligibility and confidence are computed
**deterministically** in `services/scoring.py` — never move the eligible/ineligible decision
into the prompt. That separation is the core correctness design.

## Invariants to preserve

- **Two model tiers come from settings** (`config.py`): `extraction_model` (Haiku, ingest) and
  `reasoning_model` (Sonnet, query). Don't hardcode model IDs in services.
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

Backend matching + ingestion and the eval harness (`eval/`) are code-complete and tested
(scoring unit tests + gold-set structural validation); the LLM/embedding/Supabase paths need
credentials to run end-to-end. The frontend is not built yet — see `docs/roadmap.md`.
Decision-support tool only, not medical advice; patient input is not persisted.
