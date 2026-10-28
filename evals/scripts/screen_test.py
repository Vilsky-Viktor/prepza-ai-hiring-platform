"""Tests the check that refuses a pasted text naming nothing testable for hiring (generation's
names_something_testable) on datasets/screen.json, graded by code: every text that names a
role, skills or a posting must pass (a false refusal is a failure, target none), and the
recipe, story, gibberish and instructions to an AI must be refused.

    evals/run.sh generation screen_test.py --label base     # --repeat 3

Costs well under a cent."""

import argparse
import asyncio
import json
import time

from common import DATASETS, RESULTS, cost, generation_models, load, run_record, save
from langchain_core.callbacks import get_usage_metadata_callback
from stats import share

from generation.config import settings
from generation.services.screen import names_something_testable


async def one(item: dict) -> dict:
    started = time.monotonic()
    accepted = await names_something_testable(item["text"])

    return {
        "id": item["id"],
        "accept": item["accept"],
        "accepted": accepted,
        "seconds": time.monotonic() - started,
    }


async def main(label: str, repeat: int) -> None:
    items = load(DATASETS / "screen.json")["items"]

    # A few at a time, as users send them: the check has a short timeout of its own.
    limit = asyncio.Semaphore(4)

    async def limited(item: dict) -> dict:
        async with limit:
            return await one(item)

    with get_usage_metadata_callback() as usage:
        rows = await asyncio.gather(*(limited(item) for item in items for _ in range(repeat)))

    accept = [r for r in rows if r["accept"]]
    refuse = [r for r in rows if not r["accept"]]
    scores = {
        "false_refusals": sum(not r["accepted"] for r in accept),
        "accepted": share(sum(r["accepted"] for r in accept), len(accept)),
        "refused": share(sum(not r["accepted"] for r in refuse), len(refuse)),
    }
    spent = round(sum(cost(m.split("-20")[0], u) for m, u in usage.usage_metadata.items()), 4)
    seconds = sorted(r["seconds"] for r in rows)
    run = run_record(
        model=generation_models(settings, ("screen",)),
        repeat=repeat,
        scores=scores,
        cost=spent,
        tokens=sum(u.get("total_tokens", 0) for u in usage.usage_metadata.values()),
        median_seconds=round(seconds[len(seconds) // 2], 2),
    )
    save(RESULTS / f"screen_{label}.json", {"run": run, "rows": rows})
    print(json.dumps({"scores": scores, "cost": spent, "median_seconds": run["median_seconds"]}))

    for r in rows:
        if r["accepted"] != r["accept"]:
            print(f"- {r['id']}: expected {'accept' if r['accept'] else 'refuse'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    parser.add_argument("--repeat", type=int, default=3)
    args = parser.parse_args()
    asyncio.run(main(args.label, args.repeat))
