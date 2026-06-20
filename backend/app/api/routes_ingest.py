"""POST /api/ingest — admin trigger for the ingest pipeline (X-API-Key guarded)."""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings
from app.services.ingestion import ingest_condition

router = APIRouter()


class IngestRequest(BaseModel):
    condition: str
    max_trials: int = Field(default=200, ge=1, le=1000)


@router.post("/ingest")
async def ingest(req: IngestRequest, x_api_key: str = Header(default="")) -> dict[str, object]:
    if x_api_key != get_settings().ingest_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    count = await ingest_condition(req.condition, req.max_trials)
    return {"condition": req.condition, "ingested": count}
