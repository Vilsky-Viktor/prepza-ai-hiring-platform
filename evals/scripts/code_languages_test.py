"""Tests the code-language tagging job's model call (generation's tag_examples) on
datasets/code_languages.json: the examples go in batches of TAG_BATCH_SIZE, as the job sends
them, in a new order each repeat, and each tag is graded by code against the expected notation.

    evals/run.sh generation code_languages_test.py --label base     # --repeat 3, --sample 12

Costs about $0.01 a repeat."""

import argparse
import asyncio
import json
import random
import time

from common import DATASETS, RESULTS, cost, generation_models, load, run_record, save
from langchain_core.callbacks import get_usage_metadata_callback
from stats import share

from app.config.settings import settings
from app.constants.code import TAG_BATCH_SIZE
from app.services.code_tags import tag_examples

SEED = 7


async def tag_batch(batch: list[dict]) -> tuple[list[dict], dict, float]:
    """Each item with the notation the service gave it (None when skipped), and the usage."""
    started = time.monotonic()

    with get_usage_metadata_callback() as usage:
        found = await tag_examples([item["example"] for item in batch])

    rows = [
        {"id": item["id"], "expect": item["expect"], "got": found.get(index)}
        for index, item in enumerate(batch)
    ]

    return rows, usage.usage_metadata, time.monotonic() - started


async def main(args) -> None:
    items = load(DATASETS / "code_languages.json")["items"]

    if args.sample:
        items = random.Random(SEED).sample(items, min(args.sample, len(items)))

    kinds = {item["id"]: item["kind"].split(":")[0] for item in items}
    batches = []

    for turn in range(args.repeat):
        order = random.Random(SEED + turn).sample(items, len(items))
        batches += [order[i : i + TAG_BATCH_SIZE] for i in range(0, len(order), TAG_BATCH_SIZE)]

    results = await asyncio.gather(*(tag_batch(batch) for batch in batches))
    rows = [row for found, _, _ in results for row in found]
    spent = sum(
        cost(model.split("-20")[0], used)
        for _, usage, _ in results
        for model, used in usage.items()
    )
    tokens = sum(
        used.get("input_tokens", 0) + used.get("output_tokens", 0)
        for _, usage, _ in results
        for used in usage.values()
    )
    right = [row for row in rows if row["got"] == row["expect"]]
    scores = {
        "tags": len(rows),
        "right": share(len(right), len(rows)),
        "skipped": share(sum(row["got"] is None for row in rows), len(rows)),
        "by_kind": {
            kind: share(
                sum(r["got"] == r["expect"] for r in rows if kinds[r["id"]] == kind),
                sum(kinds[r["id"]] == kind for r in rows),
            )
            for kind in sorted(set(kinds.values()))
        },
    }
    seconds = sorted(seconds for _, _, seconds in results)
    measured = {"tokens": tokens, "median_seconds": round(seconds[len(seconds) // 2], 1)}
    models = generation_models(settings, ("code_tags",))
    run = run_record(
        model=models, repeat=args.repeat, scores=scores, cost=round(spent, 4), **measured
    )
    save(RESULTS / f"code_languages_{args.label}.json", {"run": run, "rows": rows})
    print(json.dumps({"scores": scores, "cost": round(spent, 4), **measured}, indent=1))

    for row in rows:
        if row["got"] != row["expect"]:
            print(f"- {row['id']}: expected {row['expect']}, got {row['got']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    parser.add_argument("--sample", type=int, default=0)
    parser.add_argument("--repeat", type=int, default=3)
    asyncio.run(main(parser.parse_args()))
