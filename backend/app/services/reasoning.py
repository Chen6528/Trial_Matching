"""Prompt 2 call — per-criterion eligibility reasoning (Sonnet + adaptive thinking).

The system prompt is sent with `cache_control: ephemeral` so the parallel calls in a
single /match request share a cached prefix. Each call returns one evaluation per
criterion; we map them back by criterion_id (the 1-based position we sent) and default
any missing one to `unknown` so the downstream scoring never sees a gap.
"""
from __future__ import annotations

from app.config import get_settings
from app.deps import get_anthropic
from app.models.results import CriterionVerdict
from app.models.trial import Criterion
from app.prompts.evaluate_criteria import (
    CriterionEvaluations,
    build_user_message,
    SYSTEM,
)


async def evaluate_trial(patient_text: str, criteria: list[Criterion]) -> list[CriterionVerdict]:
    if not criteria:
        return []
    client = get_anthropic()
    resp = await client.messages.parse(
        model=get_settings().reasoning_model,
        # Adaptive thinking shares this budget with the visible output, so a trial with
        # many criteria can exhaust 4096 mid-JSON and truncate. Scale headroom with the
        # criteria count; only tokens actually generated are billed. Cap at 20000: the
        # SDK forces streaming above ~21333 (3600*max_tokens/128000 > 600s), which
        # messages.parse() doesn't do here.
        max_tokens=min(20000, 8192 + len(criteria) * 256),
        thinking={"type": "adaptive"},
        system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": build_user_message(patient_text, criteria)}],
        output_format=CriterionEvaluations,
    )
    parsed = resp.parsed_output
    by_id = {e.criterion_id: e for e in parsed.evaluations} if parsed else {}

    verdicts: list[CriterionVerdict] = []
    for i, c in enumerate(criteria, start=1):
        ev = by_id.get(i)
        if ev is not None:
            verdicts.append(
                CriterionVerdict(type=c.type, text=c.text, status=ev.status, reason=ev.reason)
            )
        else:
            verdicts.append(
                CriterionVerdict(
                    type=c.type, text=c.text, status="unknown", reason="Not evaluated by model."
                )
            )
    return verdicts
