"""CLI: ingest the default demo condition set end-to-end.

A convenience wrapper over scripts/ingest.py for the conditions surfaced in the frontend
datalist + eval gold set, so the demo corpus is reproducible in one command. Run from backend/:

    python scripts/ingest_all.py
    python scripts/ingest_all.py --max 100 --concurrency 1   # smaller / Windows-safe
    python scripts/ingest_all.py --condition melanoma         # override the default set
"""
from __future__ import annotations

import argparse
import asyncio

from app.services.ingestion import ingest_condition

# Mirrors CONDITION_SUGGESTIONS in frontend/components/IntakeForm.tsx.
DEFAULT_CONDITIONS = [
    "non-small cell lung cancer",
    "breast cancer",
    "melanoma",
]


async def _run(conditions: list[str], max_trials: int, concurrency: int) -> None:
    total = 0
    for condition in conditions:
        count = await ingest_condition(condition, max_trials, concurrency=concurrency)
        print(f"Ingested {count} trials for '{condition}'.")
        total += count
    print(f"Done. {total} trials across {len(conditions)} condition(s).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest the default demo condition set.")
    parser.add_argument("--max", type=int, default=200, help="Max trials per condition.")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Parallel trials in flight. Use 1 on Windows if you hit WinError 10035.",
    )
    parser.add_argument(
        "--condition",
        action="append",
        dest="conditions",
        help="Ingest this condition instead of the default set (repeatable).",
    )
    args = parser.parse_args()
    conditions = args.conditions or DEFAULT_CONDITIONS
    asyncio.run(_run(conditions, args.max, args.concurrency))


if __name__ == "__main__":
    main()
