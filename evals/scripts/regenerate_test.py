"""Tests question re-generation (a company replacing one question, and the verifier replacing a
question it can't fix): the service's own `write`, its prompt for a new question and its prompt
for options, on a fixed sample of datasets/multi_questions.json. Each is replaced by a question of
its kind, with an example when it had one, different from the other questions of its subtopic.

    evals/run.sh generation regenerate_test.py --label base [--sample 40]
    evals/run.sh generation review_questions.py results/regenerated_base.json

Writes results/regenerated_<label>.json in the question format review_questions.py reads; counts
the ones that came out and their kind. About $0.15 for 40 on gpt-6.1-sol at low."""

import argparse
import asyncio
import random
import time
import uuid

from common import DATASETS, RESULTS, cost, generation_models, is_multi, load, run_record, save
from langchain_core.callbacks import get_usage_metadata_callback
from prepza_common.examples import has_example

from app.config.settings import settings
from app.schemas.regenerate import QuestionContext
from app.services.regenerate import write

# The most other questions of a subtopic a context lists, as a topic's existing questions.
MAX_EXISTING = 9


def context_for(item: dict, items: list[dict]) -> QuestionContext:
    others = [
        other["question"]
        for other in items
        if other["subtopic"] == item["subtopic"] and other["id"] != item["id"]
    ]

    return QuestionContext(
        set_id=uuid.uuid4(),
        kind="interview",
        owner_id="eval",
        level=item["level"],
        topic=item["topic"],
        subtopics=[item["subtopic"]],
        existing=others[:MAX_EXISTING],
        multi=is_multi(item),
        example=has_example(item["question"]),
    )


async def main(label: str, sample: int) -> None:
    models = generation_models(settings)
    items = load(DATASETS / "multi_questions.json")["items"]
    chosen = random.Random(7).sample(items, sample)
    limit = asyncio.Semaphore(8)

    async def one(item: dict):
        async with limit:
            return await write(context_for(item, items), [])

    started = time.monotonic()

    with get_usage_metadata_callback() as usage:
        written = await asyncio.gather(*(one(item) for item in chosen))

    seconds = round(time.monotonic() - started)
    spent = round(sum(cost(name, data) for name, data in usage.usage_metadata.items()), 4)
    pairs = [(item, found) for item, found in zip(chosen, written, strict=True) if found]
    out = [
        {
            **{key: item[key] for key in ("domain", "level", "topic", "subtopic")},
            "id": f"r-{item['id']}",
            "question": text,
            "options": options,
        }
        for item, (text, options) in pairs
    ]
    same_kind = sum(is_multi(new) == is_multi(item) for (item, _), new in zip(pairs, out, strict=True))
    scores = {"asked": len(chosen), "written": len(out), "same_kind": same_kind}
    run = run_record(model=models, scores=scores, cost=spent, seconds=seconds)
    save(RESULTS / f"regenerated_{label}.json", {"run": run, "model": models, "items": out})
    print(f"{models}: {scores}, ${spent:.3f}, {seconds}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    parser.add_argument("--sample", type=int, default=40)
    args = parser.parse_args()
    asyncio.run(main(args.label, args.sample))
