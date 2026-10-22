"""Tests the embeddings that drop a new question asking what an earlier one asks (generation's
distinct_by_meaning, at DUPLICATE_DISTANCE) on datasets/duplicates.json: a pair that asks the
same must lose its second question, a pair that asks something else must keep both. Graded by
code; the cosine distance of each pair is saved, to see how close the threshold sits.

    evals/run.sh generation duplicates_test.py --label base

Costs well under a cent."""

import argparse
import asyncio
import json
import operator
import time

from common import DATASETS, RESULTS, load, run_record, save
from stats import share

from app.config.settings import settings
from app.constants.generation import DUPLICATE_DISTANCE
from app.integrations import llm
from app.services.dedupe import distinct_by_meaning


async def main(label: str) -> None:
    items = load(DATASETS / "duplicates.json")["items"]
    started = time.monotonic()
    kept = await asyncio.gather(*(distinct_by_meaning([i["a"], i["b"]]) for i in items))
    vectors = await llm.get_embeddings().aembed_documents(
        [t for i in items for t in (i["a"], i["b"])]
    )
    seconds = time.monotonic() - started
    rows = []

    for n, (item, found) in enumerate(zip(items, kept, strict=True)):
        a, b = vectors[2 * n], vectors[2 * n + 1]
        rows.append(
            {
                "id": item["id"],
                "same": item["same"],
                "dropped": found == [0],
                "distance": round(1 - sum(map(operator.mul, a, b)), 4),
            }
        )

    same = [r for r in rows if r["same"]]
    other = [r for r in rows if not r["same"]]
    scores = {
        "duplicates_dropped": share(sum(r["dropped"] for r in same), len(same)),
        "distinct_kept": share(sum(not r["dropped"] for r in other), len(other)),
        "threshold": DUPLICATE_DISTANCE,
    }
    run = run_record(
        model=settings.embedding_model, scores=scores, cost=0.0, seconds=round(seconds, 1)
    )
    save(RESULTS / f"duplicates_{label}.json", {"run": run, "rows": rows})
    print(json.dumps(scores, indent=1))

    for r in rows:
        if r["dropped"] != r["same"]:
            print(f"- {r['id']}: same={r['same']} dropped={r['dropped']} distance={r['distance']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    asyncio.run(main(parser.parse_args().label))
