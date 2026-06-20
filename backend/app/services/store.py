"""Supabase persistence: upsert trials + their parsed criteria, and load criteria back."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from app.deps import get_supabase
from app.models.trial import Criterion


async def upsert_trial(
    row: dict[str, Any], embedding: list[float], criteria: list[Criterion]
) -> None:
    sb = get_supabase()

    def _call():
        sb.table("trials").upsert(
            {
                "nct_id": row["nct_id"],
                "brief_title": row["brief_title"],
                "conditions": row["conditions"],
                "overall_status": row["overall_status"],
                "sex": row["sex"],
                "min_age_years": row["min_age_years"],
                "max_age_years": row["max_age_years"],
                "healthy_volunteers": row["healthy_volunteers"],
                "eligibility_criteria": row["eligibility_criteria"],
                "criteria_embedding": embedding,
                "raw_json": row["raw_json"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()
        # Replace parsed criteria wholesale so re-ingest is idempotent.
        sb.table("trial_criteria").delete().eq("nct_id", row["nct_id"]).execute()
        if criteria:
            sb.table("trial_criteria").insert(
                [
                    {
                        "nct_id": row["nct_id"],
                        "idx": i,
                        "type": c.type,
                        "category": c.category,
                        "text": c.text,
                    }
                    for i, c in enumerate(criteria)
                ]
            ).execute()

    await asyncio.to_thread(_call)


async def load_criteria(nct_ids: list[str]) -> dict[str, list[Criterion]]:
    """Fetch parsed criteria for several trials at once, grouped by nct_id, ordered by idx."""
    if not nct_ids:
        return {}
    sb = get_supabase()

    def _call():
        return (
            sb.table("trial_criteria")
            .select("nct_id, idx, type, category, text")
            .in_("nct_id", nct_ids)
            .order("idx")
            .execute()
        )

    res = await asyncio.to_thread(_call)
    grouped: dict[str, list[Criterion]] = {}
    for r in res.data or []:
        grouped.setdefault(r["nct_id"], []).append(
            Criterion(type=r["type"], category=r["category"], text=r["text"])
        )
    return grouped
