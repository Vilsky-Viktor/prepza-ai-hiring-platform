"""Tests verifier settings with the service's own key-check prompt: on datasets/key_traps.json
(the key moved to a wrong option) it should find the right option, and on the same questions with
their real key it should keep the key. Questions the reference judge found flawed are left out.

    evals/run.sh generation verify_test.py gpt-6.1-sol/low gpt-6.1-sol/medium

Each question is checked as the verifier sees it after two "wrong answer" reports. Costs about
$0.001 a check on gpt-6.1-sol (120 checks a setting, about $0.11); the service's batched checks
cost half.

With --multi, the same on datasets/multi_key_traps.json and the multi-answer questions of
datasets/multi_questions.json (a key is a set of options); questions the judge's review of that
dataset found flawed (results/reviews_datasets_multi_questions_*.json) are left out:
    evals/run.sh generation verify_test.py --multi gpt-6.1-sol/medium"""

import argparse
import asyncio
import time

from common import (
    DATASETS,
    JUDGE_EFFORT,
    JUDGE_MODEL,
    RESULTS,
    correct_options,
    cost,
    is_multi,
    load,
    model,
    reviews_of,
    run_record,
    save,
)
from langchain_core.messages import HumanMessage

from app.prompts.verify import MULTI_ANSWER_KEY, SINGLE_ANSWER_KEY, VERIFY_PROMPT
from app.schemas.verify import KeyCheck

REPORTS = "- wrong_answer: \n- wrong_answer: "


def flawed_ids(multi: bool) -> set[str]:
    """Questions a judge found flawed: the reference verdicts, or for the multi-answer dataset the
    judge's review of it, when there is one."""
    path = (
        RESULTS / f"reviews_datasets_multi_questions_{JUDGE_MODEL}_{JUDGE_EFFORT}.json"
        if multi
        else DATASETS / "reviews.json"
    )

    if not path.exists():
        return set()

    return {r["id"] for r in reviews_of(path) if not r["key_correct"] or not r["single_correct"]}


def cases(multi: bool) -> list[dict]:
    """Every trap, and the same question with its real key, as {item, expected answer}."""
    source = "multi_questions.json" if multi else "questions.json"
    originals = {item["id"]: item for item in load(DATASETS / source)["items"]}
    flawed = flawed_ids(multi)
    traps = load(DATASETS / ("multi_key_traps.json" if multi else "key_traps.json"))["items"]
    found = []

    for trap in traps:
        original = originals[trap["id"].removeprefix("trap-")]

        if original["id"] in flawed:
            continue

        right = correct_options(original)
        found.append({"kind": "trap", "item": trap, "right": right})
        found.append({"kind": "real key", "item": original, "right": right})

    return found


def prompt_for(item: dict) -> tuple[str, list[str]]:
    """The prompt, and the options in the order shown: the marked ones first, as the service
    does."""
    marked = [o["answer"] for o in item["options"] if o["correct"]]
    shown = marked + [o["answer"] for o in item["options"] if not o["correct"]]
    text = VERIFY_PROMPT.format(
        kind=MULTI_ANSWER_KEY if is_multi(item) else SINGLE_ANSWER_KEY,
        level=item["level"],
        topic=item["topic"],
        question=item["question"],
        options="\n".join(f"{n}. {answer}" for n, answer in enumerate(shown)),
        reports=REPORTS,
    )

    return text, shown


async def check(checker, case: dict) -> dict:
    text, shown = prompt_for(case["item"])
    started = time.monotonic()
    result = await checker.ainvoke([HumanMessage(content=text)])
    seconds = time.monotonic() - started
    indexes = result["parsed"].correct_indexes if result["parsed"] else None
    picked = (
        {shown[index] for index in indexes}
        if indexes and all(0 <= index < len(shown) for index in indexes)
        else None
    )

    # A key of the other kind can't be kept: the service replaces the question (checked_key).
    if picked is not None and ((len(picked) > 1) != is_multi(case["item"]) or len(picked) > 3):
        picked = None

    if picked == case["right"]:
        outcome = "right"
    elif picked is None:
        # The service replaces the question: safe, but a good question is lost when the key was right.
        outcome = "replaced"
    else:
        outcome = "wrong key"

    usage = result["raw"].usage_metadata or {}
    name = result["raw"].response_metadata["model_name"].split("-20")[0]

    return {
        "id": case["item"]["id"],
        "kind": case["kind"],
        "outcome": outcome,
        "seconds": seconds,
        "cost": cost(name, usage),
    }


def report(setting: str, results: list[dict]) -> dict:
    """Each kind's outcomes, the median time and the price of a check, printed and returned."""
    found = {}

    for kind in ("trap", "real key"):
        rows = [r for r in results if r["kind"] == kind]
        counts = {
            o: sum(r["outcome"] == o for r in rows) for o in ("right", "replaced", "wrong key")
        }
        found[kind] = {**counts, "of": len(rows)}
        print(
            f"{setting} {kind}s: {counts['right']} of {len(rows)} right, "
            f"{counts['replaced']} replaced, {counts['wrong key']} left with a wrong key"
        )

    times = sorted(r["seconds"] for r in results)
    found["median_seconds"] = round(times[len(times) // 2], 1)
    found["per_check"] = round(sum(r["cost"] for r in results) / len(results), 5)
    print(f"{setting}: median {found['median_seconds']}s; ${found['per_check']:.4f} a check")

    for r in results:
        if r["outcome"] != "right":
            print(f"  - {r['id']} ({r['kind']}): {r['outcome']}")

    return found


async def main(settings: list[str], multi: bool) -> None:
    found = cases(multi)
    print(
        f"{len(found)} checks: {len(found) // 2} traps and the same questions with their real key"
    )

    for setting in settings:
        name, effort = setting.split("/")
        checker = model(name, effort).with_structured_output(KeyCheck, include_raw=True)
        limit = asyncio.Semaphore(8)

        async def one(case, checker=checker, limit=limit):
            async with limit:
                return await check(checker, case)

        results = await asyncio.gather(*(one(case) for case in found))
        prefix = "verify_multi" if multi else "verify"
        scores = report(setting, results)
        spent = round(sum(r["cost"] for r in results), 4)
        run = run_record(model=setting, multi=multi, scores=scores, cost=spent)
        name = f"{prefix}_{setting.replace('/', '_')}.json"
        save(RESULTS / name, {"run": run, "results": results})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("settings", nargs="+", help="model/effort")
    parser.add_argument("--multi", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.settings, args.multi))
