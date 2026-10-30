"""Tests the shared question bank's filter (generation's bank_filter.is_general) on
datasets/bank_filter.json, graded by code: a private question kept (one naming or revealing an
employer, its clients, staff, tools, sites or figures, or a private person) is a leak, target
none; general questions should pass.

    evals/run.sh generation bank_filter_test.py --label base     # --repeat 3

With --local FILE (a JSON list of {"topic", "question", "options"} in results/, never
committed: companies' text) it only counts what the filter keeps and rejects, for a look at real
questions. Costs about a cent a run."""

import argparse
import asyncio
import json
import time

from common import DATASETS, RESULTS, cost, generation_models, load, run_record, save
from langchain_core.callbacks import get_usage_metadata_callback
from stats import share

from generation.config import settings
from generation.services.bank_filter import is_general


async def one(item: dict, limit: asyncio.Semaphore) -> dict:
    async with limit:
        started = time.monotonic()
        passed = await is_general(item["topic"], item["question"], item["options"])

    return {
        "id": item.get("id"),
        "general": item.get("general"),
        "passed": passed,
        "seconds": time.monotonic() - started,
    }


def scores_of(rows: list[dict]) -> dict:
    general = [r for r in rows if r["general"]]
    private = [r for r in rows if not r["general"]]

    return {
        "leaks": sum(r["passed"] for r in private),
        "private_kept_out": share(sum(not r["passed"] for r in private), len(private)),
        "general_passed": share(sum(r["passed"] for r in general), len(general)),
    }


async def main(label: str, repeat: int, local: str | None) -> None:
    items = load(RESULTS / local) if local else load(DATASETS / "bank_filter.json")["items"]
    limit = asyncio.Semaphore(4)
    # Set before the calls, so MODEL and EFFORT reach them.
    model = generation_models(settings, ("bank_filter",))

    with get_usage_metadata_callback() as usage:
        rows = await asyncio.gather(*(one(item, limit) for item in items for _ in range(repeat)))

    if local:
        scores = {"passed": share(sum(r["passed"] for r in rows), len(rows))}
    else:
        scores = scores_of(rows)

    spent = round(sum(cost(m.split("-20")[0], u) for m, u in usage.usage_metadata.items()), 4)
    seconds = sorted(r["seconds"] for r in rows)
    run = run_record(
        model=model,
        repeat=repeat,
        scores=scores,
        cost=spent,
        tokens=sum(u.get("total_tokens", 0) for u in usage.usage_metadata.values()),
        median_seconds=round(seconds[len(seconds) // 2], 2),
    )
    save(RESULTS / f"bank_filter_{label}.json", {"run": run, "rows": rows})
    print(json.dumps({"scores": scores, "cost": spent, "median_seconds": run["median_seconds"]}))

    for r in rows:
        if not local and r["passed"] != r["general"]:
            print(f"- {r['id']}: expected {'pass' if r['general'] else 'kept out'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--local")
    args = parser.parse_args()
    asyncio.run(main(args.label, args.repeat, args.local))
