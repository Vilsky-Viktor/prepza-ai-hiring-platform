"""Builds datasets/questions.json: reference questions for every subtopic in datasets/inputs.json,
written by the generation service's own prompt and model (INTERVIEW_MODEL).

Run in the generation container: evals/run.sh generation build_questions.py [--per-subtopic 5]
Costs about $0.50-1 on gpt-6.1-sol (48 subtopics), $0.09 on gpt-6-luna at high.

To test another model or effort on the same subtopics, without touching the frozen dataset:
    MODEL=gpt-6-luna EFFORT=high evals/run.sh generation build_questions.py --label luna-high
writes results/questions_<label>.json, which review_questions.py and check_code.py read; --level hard
builds only the hard domains' questions.

Multi-answer ("select all that apply") questions: --multi N asks for N of each subtopic's questions
as multi-answer, the rest single-answer, and without --label writes datasets/multi_questions.json:
    evals/run.sh generation build_questions.py --multi 3

Other languages: --inputs language_inputs.json writes datasets/language_questions.json, each
domain in its own language:
    evals/run.sh generation build_questions.py --inputs language_inputs.json --per-subtopic 6 \
        --multi 2"""

import argparse
import asyncio
import time
from collections import Counter
from datetime import UTC, datetime

from common import (
    DATASETS,
    RESULTS,
    cost,
    generation_models,
    is_multi,
    load,
    run_record,
    save,
    tokens_of,
)
from langchain_core.callbacks import get_usage_metadata_callback
from prepza_common.ai.examples import example_count

from generation.config import settings
from generation.helpers.questions import build_options, with_example
from generation.integrations import llm
from generation.schemas.questions import QuestionItemList
from generation.services.key_self_check import self_check
from generation.services.nodes.questions import focus_for, question_messages

# Multi-answer questions the self-check saw, and dropped by reason, over the run.
CHECKED = [0]
DROPPED = Counter()


async def subtopic_questions(
    domain: dict, topic: str, subtopic: str, count: int, multi: int
) -> list[dict]:
    task = {
        "level": domain["level"],
        "topic": topic,
        "subtopic": subtopic,
        "focus": focus_for(0, 1),
        "count": count,
        "multi": multi,
        "examples": example_count(count),
        "existing": [],
        "language": domain.get("language", "en"),
    }
    structured = llm.get_generation_llm().with_structured_output(QuestionItemList)
    result = await structured.ainvoke(question_messages(task))
    written = []

    for item in result.items:
        options = None if item.ambiguous else build_options(item.correct_options, item.distractors)

        if options:
            text = with_example(item.question, item.example, item.example_language)
            written.append({"text": text, "options": options})

    # The service's own self-check: multi-answer keys a blind check doesn't confirm are dropped.
    reasons = await asyncio.gather(
        *(self_check(question, topic, domain["level"]) for question in written)
    )
    DROPPED.update(reason for reason in reasons if reason)
    CHECKED[0] += sum(is_multi(question) for question in written)
    kept = [question for question, reason in zip(written, reasons) if reason is None]
    items = [
        {
            "domain": domain["id"],
            "level": domain["level"],
            "topic": topic,
            "subtopic": subtopic,
            "language": domain.get("language", "en"),
            "question": question["text"],
            "options": question["options"],
        }
        for question in kept
    ]

    return items[:count]


async def main(
    per_subtopic: int, multi: int, label: str | None, level: str | None, inputs: str
) -> None:
    models = generation_models(settings)
    domains = load(DATASETS / inputs)["domains"]
    calls = [
        (domain, topic["topic"], subtopic)
        for domain in domains
        if level is None or domain["level"] == level
        for topic in domain["topics"]
        for subtopic in topic["subtopics"]
    ]
    limit = asyncio.Semaphore(8)

    async def one(call):
        async with limit:
            return await subtopic_questions(*call, per_subtopic, multi)

    started = time.monotonic()

    with get_usage_metadata_callback() as usage:
        batches = await asyncio.gather(*(one(call) for call in calls))

    items = [item for batch in batches for item in batch]

    for index, item in enumerate(items):
        # Multi-answer datasets' ids differ from questions.json's, whose reference verdicts
        # review_questions.py compares with by id.
        item["id"] = f"{'m' if multi else 'q'}{index:04d}"

    seconds = round(time.monotonic() - started)
    spent = sum(cost(name, metadata) for name, metadata in usage.usage_metadata.items())
    dataset = "multi_questions.json" if multi else "questions.json"

    if inputs != "inputs.json":
        dataset = inputs.replace("inputs", "questions")
    save(
        RESULTS / f"questions_{label}.json" if label else DATASETS / dataset,
        {
            "about": f"Reference questions on the subtopics of {inputs}, frozen: "
            "build_questions.py writes them with the generation prompt of the date below "
            "(`run` names its commit and prompts). See datasets/README.md.",
            "model": models,
            "built": datetime.now(UTC).date().isoformat(),
            "run": run_record(
                model=models,
                cost=round(spent, 4),
                seconds=seconds,
                tokens=tokens_of(usage.usage_metadata),
            ),
            "items": items,
        },
    )
    multis = sum(is_multi(item) for item in items)
    print(
        f"{models}: {len(items)} questions ({multis} multi-answer; {CHECKED[0]} self-checked, "
        f"dropped {dict(DROPPED)}) from {len(calls)} subtopics, ${spent:.2f}, {seconds}s"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-subtopic", type=int, default=5)
    parser.add_argument("--multi", type=int, default=0, help="multi-answer ones a subtopic")
    parser.add_argument("--label", help="write results/questions_<label>.json instead")
    parser.add_argument("--level", help="only the domains of this level (with --label)")
    parser.add_argument("--inputs", default="inputs.json", help="the subtopics, in datasets/")
    args = parser.parse_args()
    asyncio.run(main(args.per_subtopic, args.multi, args.label, args.level, args.inputs))
