"""Tests verifier settings with the service's own key-check prompt: on datasets/key_traps.json
(the key moved to a wrong option) it should find the right option, and on the same questions with
their real key it should keep the key. Questions the reference judge found flawed are left out.

    evals/run.sh generation verify_test.py gpt-6.1-sol/low gpt-6.1-sol/medium

Each question is checked as the verifier sees it after two "wrong answer" reports, through the
service's own key_check_prompt and option order. Costs about
$0.001 a check on gpt-6.1-sol (120 checks a setting, about $0.11); the service's batched checks
cost half.

With --confirm, the blind confirmation a moved key needs (no option marked, a shuffled order)
on each question once: it must name the question's real key.
    evals/run.sh generation verify_test.py --confirm gpt-6.1-sol/medium

With --multi, the same on datasets/multi_key_traps.json and the multi-answer questions of
datasets/multi_questions.json (a key is a set of options); questions the judge's review of that
dataset found flawed (results/reviews_datasets_multi_questions_*.json) are left out:
    evals/run.sh generation verify_test.py --multi gpt-6.1-sol/medium"""

import argparse
import asyncio
import random
import time
import uuid

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
    tokens_of,
)
from langchain_core.callbacks import get_usage_metadata_callback
from stats import share

from generation.helpers.prompts import checker_messages
from generation.schemas.regenerate import QuestionContext, RegeneratedOption
from generation.schemas.verify import KeyCheck, QuestionQuality, ReportNote
from generation.services.verify import confirm_prompt, key_check_prompt, option_order


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


def confirm_for(item: dict) -> tuple[str, list[str]]:
    """The blind confirmation's prompt (no mark, a shuffled order), and the options as shown."""
    options = [RegeneratedOption(**o) for o in item["options"]]
    order = random.Random(f"confirm:{item['id']}").sample(range(len(options)), len(options))
    text = confirm_prompt(item["question"], options, item["level"], item["topic"], order)

    return text, [options[i].answer for i in order]


def prompt_for(item: dict) -> tuple[str, list[str]]:
    """The service's own prompt after two "wrong answer" reports, and the options in the order
    it shows them (option_order, a shuffle by the question's id)."""
    options = [RegeneratedOption(**o) for o in item["options"]]
    question = QuestionQuality(
        text=item["question"],
        options=options,
        answers=0,
        option_picks={},
        reports=[ReportNote(reason="wrong_answer", comment="")] * 2,
    )
    context = QuestionContext(
        set_id=uuid.uuid4(),
        kind="interview",
        owner_id="eval",
        level=item["level"],
        topic=item["topic"],
        subtopics=[],
        existing=[],
    )
    order = option_order(item["id"], len(options))

    return key_check_prompt(item["id"], question, context), [options[i].answer for i in order]


async def check(checker, case: dict) -> dict:
    text, shown = (confirm_for if case["kind"] == "confirm" else prompt_for)(case["item"])
    started = time.monotonic()
    result = await checker.ainvoke(checker_messages(text))
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

    for kind in sorted({r["kind"] for r in results}):
        rows = [r for r in results if r["kind"] == kind]
        counts = {
            o: sum(r["outcome"] == o for r in rows) for o in ("right", "replaced", "wrong key")
        }
        found[kind] = {**counts, "of": len(rows), "right_share": share(counts["right"], len(rows))}
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


async def main(settings: list[str], multi: bool, confirm: bool) -> None:
    found = cases(multi)

    if confirm:
        # The confirmation sees no mark, so a trap and its question read the same: one each.
        found = [{**case, "kind": "confirm"} for case in found if case["kind"] == "real key"]
        print(f"{len(found)} blind confirmations, one a question")
    else:
        print(f"{len(found)} checks: {len(found) // 2} traps and the same questions with their key")

    for setting in settings:
        name, effort = setting.split("/")
        checker = model(name, effort).with_structured_output(KeyCheck, include_raw=True)
        limit = asyncio.Semaphore(8)

        async def one(case, checker=checker, limit=limit):
            async with limit:
                return await check(checker, case)

        started = time.monotonic()

        with get_usage_metadata_callback() as usage:
            results = await asyncio.gather(*(one(case) for case in found))

        seconds = round(time.monotonic() - started)
        prefix = ("confirm" if confirm else "verify") + ("_multi" if multi else "")
        scores = report(setting, results)
        spent = round(sum(r["cost"] for r in results), 4)
        tokens = tokens_of(usage.usage_metadata)
        run = run_record(
            model=setting, multi=multi, scores=scores, cost=spent, seconds=seconds, tokens=tokens
        )
        name = f"{prefix}_{setting.replace('/', '_')}.json"
        save(RESULTS / name, {"run": run, "results": results})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("settings", nargs="+", help="model/effort")
    parser.add_argument("--multi", action="store_true")
    parser.add_argument("--confirm", action="store_true", help="the blind confirmation instead")
    args = parser.parse_args()
    asyncio.run(main(args.settings, args.multi, args.confirm))
