"""CLI: ingest one condition end-to-end.

Run from the backend/ directory so `app` is importable:
    python scripts/ingest.py --condition "non-small cell lung cancer" --max 200
"""
from __future__ import annotations

import argparse
import asyncio

from app.services.ingestion import ingest_condition


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest CT.gov trials for a condition.")
    parser.add_argument("--condition", required=True, help="e.g. 'non-small cell lung cancer'")
    parser.add_argument("--max", type=int, default=200, help="Max trials to ingest.")
    args = parser.parse_args()

    count = asyncio.run(ingest_condition(args.condition, args.max))
    print(f"Ingested {count} trials for '{args.condition}'.")


if __name__ == "__main__":
    main()
