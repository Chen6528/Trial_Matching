# Deploy runbook (v1)

Three services: **Supabase** (Postgres + pgvector), **Railway** (FastAPI backend, via the
`backend/Dockerfile`), **Vercel** (Next.js frontend). Do them in this order — the frontend
needs the backend URL, and the backend needs the database.

Prerequisites: Anthropic + OpenAI API keys, and accounts on Supabase, Railway, and Vercel.

## 1. Supabase (database)
1. Create a project (or reuse the dev one).
2. SQL editor → run `backend/app/db/schema.sql` once (creates `trials`, `trial_criteria`,
   the pgvector HNSW index, and the `match_trials` RPC).
3. Project Settings → API: copy the **Project URL** and the **service_role** key.

## 2. Populate data (ingest)
`/api/match` only returns trials that have been ingested. With `backend/.env` pointed at the
prod Supabase:
```bash
cd backend
python scripts/ingest.py --condition "non-small cell lung cancer" --max 200
# add 1–2 more for a richer demo, e.g. "melanoma", "breast cancer"
```
(Alternatively, after the backend is deployed, call `POST /api/ingest` with the `X-API-Key`
header set to `INGEST_API_KEY`.)

## 3. Railway (backend)
1. New project → deploy from this repo. Set the **root directory** to `backend/` (the
   `Dockerfile` is the build target; it reads `$PORT` automatically).
2. Variables:

   | Key | Value |
   |---|---|
   | `ANTHROPIC_API_KEY` | your key |
   | `OPENAI_API_KEY` | your key |
   | `SUPABASE_URL` | from step 1 |
   | `SUPABASE_SERVICE_KEY` | from step 1 (server-side only) |
   | `INGEST_API_KEY` | a strong secret |
   | `CORS_ORIGINS` | `https://<your-app>.vercel.app,http://localhost:3000` |

3. Deploy, then check `https://<railway-domain>/api/health` → `{"status":"ok"}`.

## 4. Vercel (frontend)
1. New project → import this repo. Set the **root directory** to `frontend/`.
2. Environment variable: `NEXT_PUBLIC_API_URL = https://<railway-domain>` (no trailing
   slash). It is read at build time, so set it before the first deploy (and redeploy if it
   changes).
3. Deploy (Vercel auto-detects Next.js).

## 5. Wire CORS + smoke test
1. Put the final Vercel domain into Railway's `CORS_ORIGINS` (plus any preview domains you
   want to allow) and redeploy the backend.
2. Open the Vercel URL → **Prefill example** → **Find matching trials** → ranked trials
   render. Confirm there are no CORS errors in the browser console.

## Notes
- `/api/match` is slow (one Sonnet reasoning call per shortlisted trial, in parallel). The
  frontend uses a 120s client timeout and talks to the backend directly — don't put a
  short-timeout serverless proxy in front of it.
- `SUPABASE_SERVICE_KEY` stays on the backend (Railway) only; the browser needs just
  `NEXT_PUBLIC_API_URL`.
- Costs scale with ingest volume (Haiku + embeddings) and match traffic (Sonnet).
