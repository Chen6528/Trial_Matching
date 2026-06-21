# Roadmap & Build Log

Phased build plan for Trial_Matching, mapped to the ~10 hr/week schedule. This is the
in-repo companion to the full design plan (folder structure, schema, prompts, risk
analysis, v1-vs-v2). Status is updated as phases land.

**Status legend:** ✅ done · 🟡 partial / in progress · ⬜ planned

**Snapshot:** Backend matching + ingestion + the eval harness are code-complete and tested, and
the Next.js frontend is built and verified end-to-end against the live local backend
(lint/build/type-check green; a sample match returns ranked trials). **Cloud deployment is
intentionally out of scope** — this is a personal project, not a hosted product; the
Railway/Vercel/Supabase runbook is kept as an optional appendix ([`deploy.md`](deploy.md)) for
if you ever want to host it. Remaining work is the **Next steps** below (Tier 1 substitutes for a
live URL — demo, CI, one-command local run — then Tier 2 depth).

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

| **Eval harness** — 65-case hand-labeled gold set (negation / threshold / biomarker / compound / temporal / missing-data) + accuracy/confusion/per-tag report, `--model` flag for the Sonnet-vs-Opus gate | `eval/gold_set.jsonl`, `eval/patients.json`, `eval/run_eval.py` |

**Done when:** `/api/match` returns ranked trials with verdicts and `run_eval.py` reports accuracy.
**Status:** code-complete and **run**: Sonnet 4.6 scored 22/22 (100%) at `reasoning_effort=low`
on the original 22-case gold set — so Prompt 2 stays on Sonnet at low effort (cheapest), no Opus
escalation needed. The gold set has since been expanded to 65 cases (see Tier 2); re-run
`run_eval.py` to score the larger set.

## Phase 3 — Week 3: Frontend ✅ (deploy descoped)
**Frontend ✅** — built and verified end-to-end against the local backend.
- Next.js 16 (App Router + TS + Tailwind v4), **single-page** flow in `app/page.tsx`
  (form → loading → results / error) — chosen over a separate results route so the rich
  POST body isn't carried across navigations.
- Components: `IntakeForm`, `TagInput`, `KeyValueInput`, `ResultsList`, `TrialCard`,
  `CriterionRow`, `EligibilityBadge`, `ConfidenceBadge`, `LoadingState`, `DisclaimerBanner`.
- `lib/types.ts` (API contract), `lib/schema.ts` (zod form + transform), `lib/api.ts`
  (direct browser→backend fetch, 120s timeout), `lib/format.ts`. CORS + loading/empty/error states done.

**Deploy — out of scope (personal project).** No live URL is a goal. The full
Railway + Vercel + Supabase prod runbook is preserved as an optional appendix:
[`deploy.md`](deploy.md), "if you ever want to host it." The practical bar instead is the
**one-command local run** (Docker Compose) in Tier 1 below.

**Done when:** `docker compose up` brings the full stack up locally and the form returns ranked trials.

## Next steps (post-core)

With the matching pipeline + frontend done and deploy descoped, the remaining work is grouped by
ROI. **Tier 1** replaces what a live URL would have shown (a demo, a green build, a runnable
app); **Tier 2** makes the quality claims credible; **Tier 3** is the interesting-but-bigger
backlog.

### Tier 1 — deployment substitutes 🟡
- **Demo GIF + architecture diagram** 🟡 — Mermaid architecture diagram + a `## Demo` section are
  in the README; the GIF itself still needs recording (prefill → match → expand criteria), e.g.
  with ScreenToGif against `docker compose up`, saved to `docs/demo.gif`.
- **CI (GitHub Actions)** ✅ — `.github/workflows/ci.yml`: backend `ruff` + `pytest`, frontend
  `lint` + `test` + `build` on every push/PR. Eval is excluded (needs a key, costs money).
- **One-command local run (Docker Compose)** ✅ — `compose.yaml` + `frontend/Dockerfile` (+ both
  `.dockerignore`s); `docker compose up --build` serves backend on :8000 + frontend on :3000.

### Tier 2 — make the quality claims credible 🟡
- **Expand the eval gold set** ✅ — grown from 22 → **65** cases across 10 patients (NSCLC, breast,
  melanoma; tags now include `compound` + `temporal`). Re-run `python eval/run_eval.py` (needs
  `ANTHROPIC_API_KEY`) to score the larger set and refresh `eval/baseline_run.json`.
- **Ingest 1–2 more conditions** 🟡 — `scripts/ingest_all.py` ingests the default set
  (NSCLC, breast cancer, melanoma) in one command; run it with credentials to populate the corpus.
- **Backend route/integration tests + frontend smoke test** ✅ — `tests/test_match_route.py`
  (`TestClient` over `/api/match`, provider seams mocked) + `tests/test_clinicaltrials.py`
  (`parse_study`); frontend `__tests__/smoke.test.tsx` (Vitest + RTL). All credential-free in CI.
  (respx wasn't usable — CT.gov uses `curl_cffi`, not httpx — so `parse_study` is unit-tested directly.)

### Tier 3 — interesting features (bigger lifts) ⬜
- **Free-text intake parsing** — paste a clinical note; Haiku (Prompt 3) → `PatientProfile`.
- **SSE streaming results** — stream each trial's verdict as it resolves instead of waiting ~30s
  for the whole fan-out.
- **Per-criterion embeddings + condition normalization** — multi-vector retrieval; lets the
  condition filter be turned back on (currently `filter_conditions=None`).
- **Per-match token/cost logging** — capture Anthropic/OpenAI usage per `/api/match`.

---

## Verified so far
- **Backend tests: 12/12 pass** (`pytest`) — scoring/ranking/age parsing, `/api/match` route
  orchestration (provider seams mocked), and CT.gov `parse_study`. `ruff` clean.
- **Frontend: 3/3 Vitest tests pass** + `npm run lint` + `npm run build` (type-check) green.
- **CI:** `.github/workflows/ci.yml` runs all of the above on every push/PR (no credentials needed).
- **Docker Compose:** `compose.yaml` + `frontend/Dockerfile` added — `docker compose up --build`
  brings up backend :8000 + frontend :3000 (live matching still needs `backend/.env` + ingested data).
- **Live end-to-end (local):** `POST /api/match` with the example NSCLC profile returns 15
  ranked trials with per-criterion verdicts + confidence, and CORS allows the frontend
  origin. The LLM / embedding / Supabase paths are exercised, not just code-complete.
- **Eval:** Sonnet 4.6 scored **22/22 (100%)** at `reasoning_effort=low` on the original 22-case
  set (negation / threshold / missing-data). Gold set since expanded to **65** cases — re-run
  `run_eval.py` to score it.

## Key decisions (the "why")
- **Structured prefilter → vector rerank → LLM**, not embedding-only shortlisting — higher precision, lower cost.
- **Tiered models:** Haiku for ingest-time criteria parsing, Sonnet for query-time reasoning; Opus only if eval accuracy falls short.
- **Eligibility is computed deterministically in code**, never by the model — the LLM only judges each criterion's statement (`met`/`not_met`/`unknown`).
- **v1 condition filter is off** (`filter_conditions=None`) — exact array-overlap on free-text condition names is brittle; the small corpus + vector rerank carry relevance. Normalized condition mapping is a v2 item.

## v1 vs v2
**v1** = the core above + Tier 1/2 next steps (2–3 oncology conditions, deterministic confidence,
runs locally via Docker Compose, no auth, ephemeral PHI). Hosting is optional and out of scope —
see [`deploy.md`](deploy.md). Tier 3 items overlap with v2 below.
**v2** = per-criterion embeddings (multi-vector retrieval), free-text LLM intake parsing, broader/live ingestion, result caching + Batch API precompute, accounts + saved searches, location filtering, observability, Haiku/Sonnet/Opus A/B with eval metrics.
