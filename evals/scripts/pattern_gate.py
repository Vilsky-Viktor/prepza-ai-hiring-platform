"""The eval gate before a quality pattern becomes a rule in use (docs/generation.md, Rules in
use): a fresh set of questions written without the rule and with it, on the same subtopics of
datasets/inputs.json, by generation's own prompt, model and self-check. Each set is judged on
every dimension (judges/question_review.md: keys of single- and multi-answer questions, clarity,
level fit, distractors, seconds to answer) and on the pattern's own mistake
(judges/pattern_failure.md, first checked on datasets/pattern_failure_traps.json). The
rule ships only if its mistake gets rarer beyond the noise and nothing else gets worse beyond it.

    evals/run.sh generation pattern_gate.py --pattern <id>             # an approved pattern
    evals/run.sh generation pattern_gate.py --pattern <id> --record    # and, if it ships, in use
    evals/run.sh generation pattern_gate.py --rule "..." --subtopics 16 --label dry   # a dry run

--record puts a pattern that ships in use with this run (its date, commit and results file);
then add its text to QUALITY_RULES (generation's prompts/quality_rules.py) and the run to
baselines/generation.md in one commit. Costs about $0.09 a subtopic (6 questions each way): about
$5 on all 53."""

import argparse
import asyncio
import random
import time
from uuid import UUID

import build_questions
import gate_checks
from common import (
    DATASETS,
    RESULTS,
    cost,
    generation_models,
    judge,
    load,
    options_text,
    prompt,
    run_record,
    save,
    tokens_of,
)
from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from review_questions import Review, review

from generation.config import settings
from generation.constants.patterns import PatternStatus
from generation.core.db import Session
from generation.helpers.prompts import learned_rules
from generation.prompts.quality_rules import QUALITY_RULES
from generation.prompts.question_rules import DISTRACTOR_RULES, LEARNED_RULES
from generation.prompts.questions import QUESTIONS_SYSTEM
from generation.repositories import patterns
from generation.services import patterns as pattern_service
from generation.services.nodes import questions as question_node

LIMIT = asyncio.Semaphore(8)


async def limited(work):
    async with LIMIT:
        return await work


class Shows(BaseModel):
    shows: bool = Field(description="The question clearly shows the mistake")


async def shows(rule: str, item: dict) -> bool:
    """Whether a question ({question, options}) shows the rule's mistake."""
    text = prompt("pattern_failure").format(
        rule=rule, question=item["question"], options=options_text(item)
    )
    result = await judge().with_structured_output(Shows).ainvoke([HumanMessage(content=text)])

    return result.shows


def traps() -> list[tuple[str, dict, bool]]:
    """The failure judge's traps (datasets/pattern_failure_traps.json), as (mistake, question,
    shows)."""
    items = load(DATASETS / "pattern_failure_traps.json")["items"]

    return [(item["mistake"], item, item["shows"]) for item in items]


async def approved_rule(pattern_id: UUID) -> str:
    async with Session() as session:
        pattern = await patterns.by_id(session, pattern_id)

    if pattern is None or pattern.status != PatternStatus.APPROVED:
        raise SystemExit(f"Pattern {pattern_id} isn't approved")

    return pattern.text


async def judge_trusted() -> str:
    """The failure judge on its traps; the gate stops unless it gets every one right."""
    found = traps()
    verdicts = await asyncio.gather(*(limited(shows(rule, item)) for rule, item, _ in found))
    right = sum(verdict == expected for verdict, (_, _, expected) in zip(verdicts, found))

    for verdict, (rule, item, expected) in zip(verdicts, found):
        if verdict != expected:
            print(f"- missed (expected {expected}): {rule} | {item['question']}")

    if right < len(found):
        raise SystemExit(f"The failure judge got {right} of {len(found)} traps right: not trusted")

    return f"{right} of {len(found)}"


def subtopics(sample: int | None) -> list[tuple]:
    calls = [
        (domain, topic["topic"], subtopic)
        for domain in load(DATASETS / "inputs.json")["domains"]
        for topic in domain["topics"]
        for subtopic in topic["subtopics"]
    ]

    return random.Random(7).sample(calls, sample) if sample and sample < len(calls) else calls


async def judged_set(rule: str, calls: list[tuple], rules: tuple[str, ...], prefix: str) -> dict:
    """Questions written under `rules`, then judged on every dimension and on the rule's mistake."""
    system = QUESTIONS_SYSTEM.replace(
        DISTRACTOR_RULES + LEARNED_RULES, DISTRACTOR_RULES + learned_rules(rules)
    )

    if (system == QUESTIONS_SYSTEM) != (rules == QUALITY_RULES):
        raise SystemExit("The rules in use aren't where the gate puts the rule: update the gate")

    question_node.QUESTIONS_SYSTEM = system
    batches = await asyncio.gather(
        *(limited(build_questions.subtopic_questions(*call, 6, 2)) for call in calls)
    )
    items = [item for batch in batches for item in batch]

    for index, item in enumerate(items):
        item["id"] = f"{prefix}{index:04d}"

    reviewer = judge().with_structured_output(Review, include_raw=True)
    reviews = await asyncio.gather(*(limited(review(reviewer, item)) for item in items))
    flags = await asyncio.gather(*(limited(shows(rule, item)) for item in items))

    return {
        "measures": gate_checks.measures(items, reviews, flags),
        "items": items,
        "reviews": reviews,
        "mistakes": flags,
    }


def table(without: dict, with_rule: dict) -> list[str]:
    lines = []

    for name, is_share, _ in gate_checks.DIMENSIONS:
        before = gate_checks.shown(without[name], is_share)
        after = gate_checks.shown(with_rule[name], is_share)
        lines.append(f"{name}: without {before}, with {after}")

    return lines


async def main(args) -> None:
    rule = await approved_rule(args.pattern) if args.pattern else args.rule
    models = generation_models(settings)
    calls = subtopics(args.subtopics)
    started = time.monotonic()

    with get_usage_metadata_callback() as usage:
        traps = await judge_trusted()
        # One after the other: each set's prompt is the node's while it's written.
        without = await judged_set(rule, calls, QUALITY_RULES, "w")
        with_rule = await judged_set(rule, calls, (*QUALITY_RULES, rule), "r")

    question_node.QUESTIONS_SYSTEM = QUESTIONS_SYSTEM
    seconds = round(time.monotonic() - started)
    spent = round(sum(cost(name, used) for name, used in usage.usage_metadata.items()), 4)
    ships, reasons = gate_checks.decision(without["measures"], with_rule["measures"])
    lines = table(without["measures"], with_rule["measures"])
    name = f"gate_{args.label or args.pattern}.json"
    run = run_record(
        model=models,
        rule=rule,
        pattern=str(args.pattern) if args.pattern else None,
        subtopics=len(calls),
        judge_traps=traps,
        scores=lines,
        ships=ships,
        reasons=reasons,
        cost=spent,
        seconds=seconds,
        tokens=tokens_of(usage.usage_metadata),
    )
    save(RESULTS / name, {"run": run, "without": without, "with": with_rule})
    print("\n".join([f"{rule}", f"judge traps {traps}", *lines]))
    print(
        f"{'ships' if ships else 'does not ship: ' + '; '.join(reasons)}; ${spent:.2f}, {seconds}s"
    )

    if args.record and args.pattern and ships:
        await pattern_service.put_in_use(args.pattern, f"{run['date']} {run['commit']} {name}")
        print("In use: add its text to QUALITY_RULES and the run to baselines/generation.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    chosen = parser.add_mutually_exclusive_group(required=True)
    chosen.add_argument("--pattern", type=UUID, help="an approved pattern's id")
    chosen.add_argument("--rule", help="a rule's text, for a dry run (never recorded)")
    parser.add_argument("--subtopics", type=int, help="a fixed sample of the subtopics")
    parser.add_argument("--label", help="the results file's name, gate_<label>.json")
    parser.add_argument("--record", action="store_true", help="put a pattern that ships in use")
    asyncio.run(main(parser.parse_args()))
