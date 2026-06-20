"""Per-criterion reasoning eval — the negation/threshold accuracy proof.

Runs Prompt 2 (`services.reasoning.evaluate_trial`) over a hand-labeled gold set and
reports accuracy, a confusion matrix, and per-tag breakdowns. Criteria are batched per
patient (one model call per patient), exactly as production /match does.

Only needs ANTHROPIC_API_KEY (no Supabase/OpenAI). Run from backend/:

    python eval/run_eval.py
    python eval/run_eval.py --model claude-opus-4-8        # Sonnet-vs-Opus gate
    python eval/run_eval.py --min-accuracy 0.9 --json-out eval/last_run.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import defaultdict
from pathlib import Path

# Allow `python eval/run_eval.py` without an editable install.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.models.patient import PatientProfile  # noqa: E402
from app.models.trial import Criterion  # noqa: E402
from app.services.reasoning import evaluate_trial  # noqa: E402

EVAL_DIR = Path(__file__).resolve().parent
STATUSES = ["met", "not_met", "unknown"]


def load_gold() -> tuple[dict, list[dict]]:
    patients = json.loads((EVAL_DIR / "patients.json").read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in (EVAL_DIR / "gold_set.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return patients, rows


async def _evaluate_patient(pid: str, profile_data: dict, rows: list[dict]) -> list[dict]:
    profile = PatientProfile(**profile_data)
    criteria = [Criterion(**r["criterion"]) for r in rows]
    verdicts = await evaluate_trial(profile.to_text(), criteria)
    return [
        {
            "patient_id": pid,
            "tag": r.get("tag", "untagged"),
            "text": r["criterion"]["text"],
            "expected": r["expected"],
            "predicted": v.status,
            "reason": v.reason,
            "correct": v.status == r["expected"],
        }
        for r, v in zip(rows, verdicts)
    ]


async def run(model: str | None) -> list[dict]:
    if model:
        get_settings().reasoning_model = model
    patients, rows = load_gold()
    by_pid: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_pid[r["patient_id"]].append(r)
    nested = await asyncio.gather(
        *(_evaluate_patient(pid, patients[pid], prows) for pid, prows in by_pid.items())
    )
    return [item for sub in nested for item in sub]


def report(results: list[dict], model: str) -> float:
    total = len(results)
    correct = sum(r["correct"] for r in results)
    acc = correct / total if total else 0.0

    print(f"\nModel: {model}")
    print(f"Overall accuracy: {correct}/{total} = {acc:.1%}\n")

    by_tag: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for r in results:
        by_tag[r["tag"]][0] += int(r["correct"])
        by_tag[r["tag"]][1] += 1
    print("By tag:")
    for tag, (c, t) in sorted(by_tag.items()):
        print(f"  {tag:16s} {c}/{t} = {c / t:.0%}")

    print("\nConfusion (rows = expected, cols = predicted):")
    print(" " * 12 + "".join(f"{s:>10}" for s in STATUSES))
    mat = {e: {p: 0 for p in STATUSES} for e in STATUSES}
    for r in results:
        if r["expected"] in mat and r["predicted"] in STATUSES:
            mat[r["expected"]][r["predicted"]] += 1
    for e in STATUSES:
        print(f"  {e:10s}" + "".join(f"{mat[e][p]:>10}" for p in STATUSES))

    misses = [r for r in results if not r["correct"]]
    if misses:
        print(f"\nMismatches ({len(misses)}):")
        for m in misses:
            print(f"  [{m['patient_id']}/{m['tag']}] expected={m['expected']} got={m['predicted']}")
            print(f"      criterion: {m['text']}")
            print(f"      model reason: {m['reason']}")

    return acc


def main() -> None:
    ap = argparse.ArgumentParser(description="Per-criterion reasoning eval.")
    ap.add_argument("--model", default=None, help="Override reasoning model, e.g. claude-opus-4-8")
    ap.add_argument("--min-accuracy", type=float, default=None, help="Exit 1 if below this.")
    ap.add_argument("--json-out", default=None, help="Write per-case results to this JSON path.")
    args = ap.parse_args()

    results = asyncio.run(run(args.model))
    acc = report(results, get_settings().reasoning_model)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(results, indent=2), encoding="utf-8")
    if args.min_accuracy is not None and acc < args.min_accuracy:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
