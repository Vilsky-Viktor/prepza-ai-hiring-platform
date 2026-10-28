"""Tests the weekly quality pattern job's model call (generation's find_patterns) on
datasets/patterns.json: each group of flagged questions goes to the service's own prompt and
model, its rules pass the service's own checks (enough questions, length, no names, no quotes),
and each kept rule is matched to a planted mistake by the questions it lists (at least
MIN_PATTERN_QUESTIONS of the planted ones) and by a judge (judges/pattern_match.md). A kept rule
that matches no planted mistake may still be right (made-up questions share more than was
planted): a second judge (judges/pattern_support.md) decides whether the questions it cites show
it. The matching judge is checked every run on the dataset's judge_traps.

    evals/run.sh generation patterns_test.py --label base      # --repeat 3, --only g1,g4

Costs about $0.10 a repeat."""

import argparse
import asyncio
import json
import time

from common import (
    DATASETS,
    JUDGE_MODEL,
    RESULTS,
    cost,
    generation_models,
    judge,
    load,
    prompt,
    run_record,
    save,
)
from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from stats import share

from generation.config import settings
from generation.constants.patterns import MIN_PATTERN_QUESTIONS
from generation.helpers.patterns import question_block
from generation.schemas.patterns import QualitySignal
from generation.services.patterns import find_patterns, rejection


class Match(BaseModel):
    same: bool = Field(description="The rule names the planted mistake")


class Support(BaseModel):
    supported: bool = Field(description="Every cited question shows the rule's mistake")


async def supported(rule: dict, signals: list[QualitySignal]) -> tuple[bool, float]:
    questions = "\n\n".join(question_block(n, signals[n - 1]) for n in rule["questions"])
    text = prompt("pattern_support").format(questions=questions, rule=rule["text"])
    result = (
        await judge()
        .with_structured_output(Support, include_raw=True)
        .ainvoke([HumanMessage(content=text)])
    )

    return result["parsed"].supported, cost(JUDGE_MODEL, result["raw"].usage_metadata or {})


async def same(planted: str, rule: str) -> tuple[bool, float]:
    result = (
        await judge()
        .with_structured_output(Match, include_raw=True)
        .ainvoke([HumanMessage(content=prompt("pattern_match").format(planted=planted, rule=rule))])
    )

    return result["parsed"].same, cost(JUDGE_MODEL, result["raw"].usage_metadata or {})


async def run_group(group: dict, turn: int) -> dict:
    signals = [QualitySignal(flag=group["flag"], **item) for item in group["questions"]]
    started = time.monotonic()

    with get_usage_metadata_callback() as usage:
        result = await find_patterns(group["flag"], signals, group["known"])

    seconds = time.monotonic() - started
    kept = []

    for proposed in result.patterns:
        numbers = {n for n in proposed.questions if 1 <= n <= len(signals)}

        # As the service: a known pattern named by its number counts as that pattern, whatever
        # its text; a new one must pass the checks.
        known = (
            group["known"][proposed.same_as - 1]
            if proposed.same_as and 1 <= proposed.same_as <= len(group["known"])
            else None
        )

        if len(numbers) < MIN_PATTERN_QUESTIONS:
            continue

        if known or rejection(proposed, signals) is None:
            rule = {"text": known or proposed.text, "questions": sorted(numbers)}
            kept.append({**rule, "same_as": proposed.same_as})

    judge_cost = 0.0
    found = {}

    for planted in group["planted"]:
        for rule in kept:
            if len(set(rule["questions"]) & set(planted["questions"])) < MIN_PATTERN_QUESTIONS:
                continue

            match, spent = await same(planted["mistake"], rule["text"])
            judge_cost += spent

            if match:
                found[planted["id"]] = rule
                rule["planted"] = planted["id"]

                break

    for rule in kept:
        if "planted" not in rule:
            rule["supported"], spent = await supported(rule, signals)
            judge_cost += spent

    known_right = [
        found[p["id"]]["same_as"] == p["same_as"]
        for p in group["planted"]
        if "same_as" in p and p["id"] in found
    ]

    return {
        "group": group["id"],
        "turn": turn,
        "kept": kept,
        "found": sorted(found),
        "planted": [p["id"] for p in group["planted"]],
        "unsupported": sum(not rule.get("supported", True) for rule in kept),
        "known_right": known_right,
        "forbidden": any(
            word.lower() in rule["text"].lower()
            for word in group.get("forbidden", [])
            for rule in kept
        ),
        "cost": sum(cost(m.split("-20")[0], u) for m, u in usage.usage_metadata.items()),
        "tokens": sum(
            u.get("input_tokens", 0) + u.get("output_tokens", 0)
            for u in usage.usage_metadata.values()
        ),
        "judge_cost": judge_cost,
        "seconds": seconds,
    }


async def judge_traps(traps: list[dict]) -> tuple[dict, float]:
    """The matching judge on pairs with known verdicts: matches found and mismatches refused."""
    results = await asyncio.gather(*(same(t["planted"], t["rule"]) for t in traps))
    caught = {
        kind: f"{sum(m == t['same'] for t, (m, _) in zip(traps, results, strict=True) if t['same'] is kind)}"
        f" of {sum(t['same'] is kind for t in traps)}"
        for kind in (True, False)
    }

    return {"match": caught[True], "no_match": caught[False]}, sum(s for _, s in results)


async def main(args) -> None:
    data = load(DATASETS / "patterns.json")
    groups = [g for g in data["groups"] if not args.only or g["id"] in args.only.split(",")]
    rows = await asyncio.gather(
        *(run_group(g, turn) for g in groups for turn in range(args.repeat))
    )
    caught, trap_cost = await judge_traps(data["judge_traps"])
    planted = sum(len(r["planted"]) for r in rows)
    kept = sum(len(r["kept"]) for r in rows)
    none_groups = [r for r in rows if not r["planted"]]
    known = [ok for r in rows for ok in r["known_right"]]
    scores = {
        "planted_found": share(sum(len(r["found"]) for r in rows), planted),
        "kept_rules_supported": share(kept - sum(r["unsupported"] for r in rows), kept),
        "no_rule_when_none": share(sum(not r["kept"] for r in none_groups), len(none_groups)),
        "known_named": share(sum(known), len(known)),
        "instruction_followed": sum(r["forbidden"] for r in rows),
        "judge_traps_caught": caught,
    }
    spent = {
        "patterns": round(sum(r["cost"] for r in rows), 4),
        "judge": round(sum(r["judge_cost"] for r in rows) + trap_cost, 4),
    }
    seconds = sorted(r["seconds"] for r in rows)
    measured = {
        "tokens": sum(r["tokens"] for r in rows),
        "median_seconds": round(seconds[len(seconds) // 2], 1),
    }
    models = generation_models(settings, ("patterns",))
    run = run_record(model=models, repeat=args.repeat, scores=scores, cost=spent, **measured)
    save(RESULTS / f"patterns_{args.label}.json", {"run": run, "rows": rows})
    print(json.dumps({"scores": scores, "cost": spent, **measured}, indent=1))

    for r in rows:
        missed = sorted(set(r["planted"]) - set(r["found"]))
        extra = [rule["text"] for rule in r["kept"] if not rule.get("supported", True)]

        if missed or extra:
            print(f"- {r['group']} ({r['turn']}): missed {missed}; unsupported {extra}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    parser.add_argument("--only", default="")
    parser.add_argument("--repeat", type=int, default=3)
    asyncio.run(main(parser.parse_args()))
