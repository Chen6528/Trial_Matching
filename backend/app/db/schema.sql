-- Clinical trial matching — Supabase schema.
-- Run this once in the Supabase SQL editor (or via `supabase db` tooling).

create extension if not exists vector;

-- One row per trial. Structured fields drive the SQL prefilter; the embedding
-- drives the vector rerank; raw_json is kept for audit/reprocessing.
create table if not exists trials (
  nct_id               text primary key,
  brief_title          text,
  conditions           text[],
  overall_status       text,                 -- RECRUITING, NOT_YET_RECRUITING, ...
  sex                  text,                  -- ALL | MALE | FEMALE
  min_age_years        numeric,               -- parsed from e.g. "18 Years" (null if N/A)
  max_age_years        numeric,
  healthy_volunteers   boolean,
  eligibility_criteria text,                  -- raw free-text blob (audit/debug)
  criteria_embedding   vector(1536),          -- OpenAI text-embedding-3-small
  raw_json             jsonb,
  fetched_at           timestamptz default now(),
  updated_at           timestamptz default now()
);

-- Atomic, normalized criteria produced by the extraction pass (Prompt 1).
create table if not exists trial_criteria (
  id        bigint generated always as identity primary key,
  nct_id    text references trials(nct_id) on delete cascade,
  idx       int,
  type      text,   -- inclusion | exclusion
  category  text,   -- demographics|condition|biomarker|prior_treatment|lab|comorbidity|performance_status|other
  text      text
);

create index if not exists idx_trial_criteria_nct on trial_criteria (nct_id);
create index if not exists idx_trials_conditions on trials using gin (conditions);
-- HNSW cosine index for the vector rerank.
create index if not exists idx_trials_embedding on trials using hnsw (criteria_embedding vector_cosine_ops);

-- Structured prefilter (status + condition + age/sex) AND vector rerank in one call.
-- Exposed to the backend via PostgREST RPC: supabase.rpc("match_trials", {...}).
create or replace function match_trials(
  query_embedding   vector(1536),
  match_count       int     default 15,
  filter_conditions text[]  default null,
  patient_sex       text    default null,
  patient_age       numeric default null
)
returns table (nct_id text, brief_title text, similarity float)
language sql stable
as $$
  select t.nct_id,
         t.brief_title,
         1 - (t.criteria_embedding <=> query_embedding) as similarity   -- <=> = cosine distance
  from trials t
  where t.overall_status in ('RECRUITING', 'NOT_YET_RECRUITING')
    and (filter_conditions is null or t.conditions && filter_conditions)
    and (patient_sex is null or t.sex in ('ALL', patient_sex))
    and (patient_age is null or (
          (t.min_age_years is null or patient_age >= t.min_age_years) and
          (t.max_age_years is null or patient_age <= t.max_age_years)))
  order by t.criteria_embedding <=> query_embedding
  limit match_count;
$$;
