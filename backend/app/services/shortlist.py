"""Structured prefilter + pgvector rerank via the `match_trials` Supabase RPC."""
from __future__ import annotations

import asyncio
from typing import Any

from app.config import get_settings
from app.deps import get_supabase
from app.models.patient import PatientProfile


async def shortlist(
    profile: PatientProfile,
    query_embedding: list[float],
    match_count: int | None = None,
) -> list[dict[str, Any]]:
    """Return up to `match_count` candidate trials: [{nct_id, brief_title, similarity}].

    Condition filtering is intentionally left off in v1 (filter_conditions=None): the
    ingested corpus is small and the embedding rerank handles topical relevance.
    Exact array-overlap on free-text condition names is brittle — v2 adds a normalized
    condition map. Age/sex still prefilter in SQL.
    """
    settings = get_settings()
    sb = get_supabase()
    params = {
        "query_embedding": query_embedding,
        "match_count": match_count or settings.shortlist_size,
        "patient_sex": profile.sex,
        "patient_age": profile.age,
        "filter_conditions": None,
    }

    def _call():
        return sb.rpc("match_trials", params).execute()

    res = await asyncio.to_thread(_call)
    return res.data or []
