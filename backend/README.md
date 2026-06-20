# Backend — Clinical Trial Matching API

FastAPI service: ClinicalTrials.gov v2 retrieval → criteria normalization (Claude Haiku) →
OpenAI embeddings in Supabase/pgvector → structured prefilter + vector rerank →
per-criterion eligibility reasoning (Claude Sonnet) → deterministic confidence scoring.

## Prerequisites
- Python 3.11+
- A Supabase project, an OpenAI API key, and an Anthropic API key

## Setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows  (use: source .venv/bin/activate on macOS/Linux)
pip install -e ".[dev]"
copy .env.example .env            # then fill in keys  (cp on macOS/Linux)
```

## Database
Run `app/db/schema.sql` once in the Supabase SQL editor (creates the `trials` /
`trial_criteria` tables, the pgvector HNSW index, and the `match_trials` RPC).

## Ingest trials
```bash
python scripts/ingest.py --condition "non-small cell lung cancer" --max 200
python scripts/ingest.py --condition "breast cancer" --max 200
```
This fetches recruiting trials, normalizes their criteria, embeds them, and upserts to Supabase.

## Run the API
```bash
uvicorn app.main:app --reload
# Swagger UI: http://localhost:8000/docs
```

Example match request:
```bash
curl -X POST http://localhost:8000/api/match -H "Content-Type: application/json" -d '{
  "age": 62, "sex": "MALE", "condition": "non-small cell lung cancer", "stage": "IV",
  "biomarkers": ["EGFR positive"], "prior_treatments": ["platinum chemotherapy"],
  "ecog_status": 1, "lab_values": {"eGFR": "72 mL/min"}
}'
```

## Test
```bash
pytest                 # pure-logic tests (scoring, ranking, age parsing) need no credentials
```

## Eval (per-criterion reasoning accuracy)
Measures whether Prompt 2 gets each criterion right, weighted toward negations, numeric
thresholds, and missing-data cases. Needs only `ANTHROPIC_API_KEY`.
```bash
python eval/run_eval.py                        # accuracy + confusion matrix + per-tag breakdown
python eval/run_eval.py --model claude-opus-4-8  # Sonnet-vs-Opus comparison
```
Edit `eval/gold_set.jsonl` + `eval/patients.json` to grow the labeled set.

## Routes
- `POST /api/match` — rank trials with per-criterion verdicts + confidence
- `GET  /api/trials/{nct_id}` — trial detail + parsed criteria
- `POST /api/ingest` — admin ingest (header `X-API-Key: <INGEST_API_KEY>`)
- `GET  /api/health` — liveness

## Deploy (Railway)
Point Railway at this directory; the `Dockerfile` builds and serves on `$PORT`. Set the
same env vars as `.env`. Add your Vercel URL to `CORS_ORIGINS`.

## Layout
```
app/
  api/        FastAPI routers
  models/     Pydantic: PatientProfile, Trial, Criterion, MatchResponse
  prompts/    Prompt 1 (extract) & Prompt 2 (evaluate) text + output schemas
  services/   clinicaltrials, extraction, embeddings, shortlist, reasoning, scoring, store, ingestion
  db/         schema.sql
scripts/      ingest CLI
tests/        scoring/parse unit tests
```
