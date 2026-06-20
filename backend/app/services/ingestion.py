"""End-to-end ingest pipeline: CT.gov fetch -> Prompt 1 parse -> embed -> upsert.

Shared by POST /api/ingest and scripts/ingest.py. Bounded concurrency keeps us polite
to the CT.gov, OpenAI, and Anthropic APIs.
"""
from __future__ import annotations

import asyncio
from typing import Any

from app.services.clinicaltrials import fetch_studies
from app.services.embeddings import embed_text
from app.services.extraction import extract_criteria
from app.services.store import upsert_trial


def _embedding_input(row: dict[str, Any]) -> str:
    conditions = ", ".join(row.get("conditions") or [])
    pieces = [
        row.get("brief_title") or "",
        f"Conditions: {conditions}" if conditions else "",
        row.get("eligibility_criteria") or "",
    ]
    return "\n".join(p for p in pieces if p)


async def _process_one(row: dict[str, Any], sem: asyncio.Semaphore) -> None:
    async with sem:
        criteria = await extract_criteria(row["eligibility_criteria"])
        embedding = await embed_text(_embedding_input(row))
        await upsert_trial(row, embedding, criteria)


async def ingest_condition(
    condition: str, max_trials: int = 200, concurrency: int = 5
) -> int:
    rows = await fetch_studies(condition, max_trials)
    sem = asyncio.Semaphore(concurrency)
    await asyncio.gather(*(_process_one(r, sem) for r in rows))
    return len(rows)
