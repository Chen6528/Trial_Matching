"""GET /api/trials/{nct_id} — single trial detail + parsed criteria (no LLM call)."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from app.deps import get_supabase
from app.models.trial import Trial
from app.services.store import load_criteria

router = APIRouter()


@router.get("/trials/{nct_id}", response_model=Trial)
async def get_trial(nct_id: str) -> Trial:
    sb = get_supabase()

    def _call():
        return sb.table("trials").select("*").eq("nct_id", nct_id).limit(1).execute()

    res = await asyncio.to_thread(_call)
    if not res.data:
        raise HTTPException(status_code=404, detail="Trial not found")

    row = res.data[0]
    criteria_map = await load_criteria([nct_id])
    return Trial(
        nct_id=row["nct_id"],
        brief_title=row.get("brief_title"),
        conditions=row.get("conditions") or [],
        overall_status=row.get("overall_status"),
        sex=row.get("sex"),
        min_age_years=row.get("min_age_years"),
        max_age_years=row.get("max_age_years"),
        healthy_volunteers=row.get("healthy_volunteers"),
        eligibility_criteria=row.get("eligibility_criteria"),
        criteria=criteria_map.get(nct_id, []),
    )
