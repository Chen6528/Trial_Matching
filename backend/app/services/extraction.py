"""Prompt 1 call — normalize raw eligibility text into atomic criteria (Haiku)."""
from __future__ import annotations

from app.config import get_settings
from app.deps import get_anthropic
from app.models.trial import Criterion
from app.prompts.extract_criteria import ParsedCriteria, build_user_message, SYSTEM


async def extract_criteria(raw_criteria: str) -> list[Criterion]:
    if not raw_criteria or not raw_criteria.strip():
        return []
    client = get_anthropic()
    resp = await client.messages.parse(
        model=get_settings().extraction_model,
        max_tokens=4096,
        system=SYSTEM,
        messages=[{"role": "user", "content": build_user_message(raw_criteria)}],
        output_format=ParsedCriteria,
    )
    parsed = resp.parsed_output
    if not parsed:
        return []
    return [Criterion(type=c.type, category=c.category, text=c.text) for c in parsed.criteria]
