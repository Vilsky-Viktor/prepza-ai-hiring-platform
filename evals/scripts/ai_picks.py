"""AI-trap questions (internal_docs/plans/anti-cheating.md, signal 3): how often AI models, asked
a question as a candidate relaying it would ask, agree on the same wrong option while the
reference judge finds the key right, and how often a candidate's AI then picks that option.

    evals/run.sh generation ai_picks.py --build      # model calls, about $1.1; freezes the picks
    evals/run.sh generation ai_picks.py              # free: the metrics from the frozen picks

The pick models (PICKS) answer each question once, in one option order, as generation would; a
question where all of them pick the same wrong answer is a trap candidate, and it's kept only when
the verifier's blind check (its own prompt, a new order) names the marked key, so it's fair. The
relay models (RELAYS) answer again in another order, standing in for a candidate's AI app: the
share of traps where they pick the trap's option is what the AI-trap signal could catch.

AI-trap questions were dropped on this measurement (evals/README.md, 2026-10-29: the pick models
never agree on a wrong answer). The script stays to rerun it on a new model, and its relays'
answers are what integrity_signals.py's relaying candidates give."""

import argparse
import asyncio
import random
import time

from ai_pick_prompt import AI_PICK_PROMPT, MULTI_NOTE
from common import (
    DATASETS,
    JUDGE_EFFORT,
    JUDGE_MODEL,
    RESULTS,
    correct_options,
    cost,
    load,
    model,
    question_items,
    reviews_of,
    run_record,
    save,
)
from stats import share

NAME = "ai_picks.json"
SETS = ("questions.json", "multi_questions.json", "language_questions.json")
# The models generation would ask: the cheapest answering at once, as a free AI app does, and
# the main model thinking briefly.
PICKS = ("gpt-6-luna/none", "gpt-6.1-sol/low")
# A candidate's AI app: the same models asked again in another order, and a reasoning setting.
RELAYS = ("gpt-6-luna/none", "gpt-6.1-sol/low", "gpt-6-luna/medium")
VERIFIER = "gpt-6.1-sol/medium"
AT_ONCE = 12


def judged_right(name: str) -> dict[str, bool]:
    """The reference judge's verdict on each question's key (and single defensible answer)."""
    path = (
        DATASETS / "reviews.json"
        if name == "questions.json"
        else RESULTS
        / f"reviews_datasets_{name.removesuffix('.json')}_{JUDGE_MODEL}_{JUDGE_EFFORT}.json"
    )

    return {r["id"]: r["key_correct"] and r["single_correct"] for r in reviews_of(path)}


def pick_prompt(item: dict, order: list[int]) -> str:
    multi = len(correct_options(item)) > 1

    return AI_PICK_PROMPT.format(
        question=item["question"],
        options="\n".join(
            f"{number}. {item['options'][i]['answer']}" for number, i in enumerate(order, 1)
        ),
        note=MULTI_NOTE if multi else "",
    )


async def ask(llm, item: dict, seed: str, verify: bool = False) -> dict:
    """One model's answer, as option indexes in the question's own order; None when it gave
    none or an option that isn't there."""
    from generation.helpers.prompts import checker_messages
    from generation.schemas.regenerate import RegeneratedOption
    from generation.services.verify import confirm_prompt

    count = len(item["options"])
    order = random.Random(seed).sample(range(count), count)

    if verify:
        options = [RegeneratedOption(**option) for option in item["options"]]
        messages = checker_messages(
            confirm_prompt(item["question"], options, item["level"], item["topic"], order)
        )
        shift = 0
    else:
        messages = [("user", pick_prompt(item, order))]
        shift = 1

    result = await llm.ainvoke(messages)
    parsed = result["parsed"]
    indexes = parsed.correct_indexes if parsed else None
    picked = None

    if indexes and all(0 <= index - shift < count for index in indexes):
        picked = sorted({order[index - shift] for index in indexes})

    usage = result["raw"].usage_metadata or {}
    name = result["raw"].response_metadata["model_name"].split("-20")[0]

    return {"picked": picked, "cost": cost(name, usage)}


async def run_setting(setting: str, items: list[dict], tag: str, verify: bool = False) -> list:
    from generation.schemas.verify import KeyCheck

    name, effort = setting.split("/")
    llm = model(name, effort).with_structured_output(KeyCheck, include_raw=True)
    limit = asyncio.Semaphore(AT_ONCE)

    async def one(item):
        async with limit:
            return await ask(llm, item, f"{tag}:{item['id']}", verify)

    return await asyncio.gather(*(one(item) for item in items))


def right_set(item: dict) -> list[int]:
    return sorted(i for i, option in enumerate(item["options"]) if option["correct"])


def trap_option(entry: dict, item: dict, rule: str = "agree") -> list[int] | None:
    """The trap's wrong answer. "agree", as planned: the one every pick model gave, when they all
    gave the same one. "cheap": the cheapest model's wrong answer on a question the main model
    answers right (the only traps there are, as the main model gets nearly every one right)."""
    if rule == "cheap":
        cheap, main = (entry["picks"][setting] for setting in PICKS)

        return cheap if cheap is not None and cheap != right_set(item) == main else None

    picks = [entry["picks"][setting] for setting in PICKS]

    if any(pick is None for pick in picks) or any(pick != picks[0] for pick in picks):
        return None

    return picks[0] if picks[0] != right_set(item) else None


async def build() -> None:
    started, spent = time.monotonic(), 0.0
    items = [(name, item) for name in SETS for item in question_items(DATASETS / name)]
    entries = [{"set": name, "id": item["id"], "picks": {}, "relays": {}} for name, item in items]

    for group, settings, tag in (("picks", PICKS, "a"), ("relays", RELAYS, "b")):
        for setting in settings:
            answers = await run_setting(setting, [item for _, item in items], tag)
            spent += sum(answer["cost"] for answer in answers)

            for entry, answer in zip(entries, answers, strict=True):
                entry[group][setting] = answer["picked"]

            print(f"{group} {setting}: done, ${spent:.3f} so far")

    candidates = [
        (entry, item)
        for entry, (_, item) in zip(entries, items, strict=True)
        if trap_option(entry, item)
    ]
    checks = await run_setting(VERIFIER, [item for _, item in candidates], "v", verify=True)
    spent += sum(check["cost"] for check in checks)

    for (entry, _), check in zip(candidates, checks, strict=True):
        entry["verifier"] = check["picked"]

    save(
        DATASETS / NAME,
        {
            "about": "Each question of the question sets answered blind by AI models: the pick "
            "models in one option order, the relay models in another, and the verifier's blind "
            "check on the questions where every pick model gave the same wrong answer.",
            "built": run_record(cost=round(spent, 4))["date"],
            "model": {"picks": PICKS, "relays": RELAYS, "verifier": VERIFIER},
            "run": run_record(cost=round(spent, 4), seconds=round(time.monotonic() - started)),
            "items": entries,
        },
    )


def kept_trap(entry: dict, item: dict, rule: str) -> bool:
    """Fair to people: the verifier's blind check names the key ("agree"), or the main model
    already did ("cheap")."""
    if rule == "cheap":
        return True

    return entry.get("verifier") == right_set(item)


def measure(entries: list[dict], questions: dict, verdicts: dict, rule: str) -> dict:
    total = len(entries)
    candidates, traps, unfair, hits = [], [], [], {setting: 0 for setting in RELAYS}
    right = {setting: 0 for setting in RELAYS}

    for entry in entries:
        item = questions[(entry["set"], entry["id"])]

        for setting in RELAYS:
            right[setting] += entry["relays"][setting] == right_set(item)

        option = trap_option(entry, item, rule)

        if option is None:
            continue

        candidates.append(entry["id"])
        # A question the judge didn't review (part of the language set) isn't counted against.
        fair = verdicts[entry["set"]].get(entry["id"], True)
        kept = kept_trap(entry, item, rule)

        if kept and not fair:
            unfair.append(entry["id"])

        if not kept:
            continue

        traps.append(entry["id"])

        for setting in RELAYS:
            hits[setting] += entry["relays"][setting] == option

    return {
        "questions": total,
        "candidates": share(len(candidates), total),
        "traps": share(len(traps), total),
        "kept_but_judge_found_key_wrong": unfair,
        "relay_right": {setting: share(right[setting], total) for setting in RELAYS},
        "relay_picks_trap": {setting: share(hits[setting], len(traps)) for setting in RELAYS},
    }


def main() -> None:
    data = load(DATASETS / NAME)
    questions = {
        (name, item["id"]): item for name in SETS for item in question_items(DATASETS / name)
    }
    verdicts = {name: judged_right(name) for name in SETS}
    entries = data["items"]
    scores = {}

    for rule in ("agree", "cheap"):
        found = {"all": measure(entries, questions, verdicts, rule)}

        for name in SETS:
            chosen = [e for e in entries if e["set"] == name]
            found[name] = measure(chosen, questions, verdicts, rule)

        for level in ("basic", "medium", "hard"):
            chosen = [e for e in entries if questions[(e["set"], e["id"])]["level"] == level]
            found[level] = measure(chosen, questions, verdicts, rule)

        scores[rule] = found

    print(scores)
    run = run_record(dataset=NAME, scores=scores, cost=0)
    save(RESULTS / NAME, {"run": run, "built": data["run"]})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", help="ask the models (about $1.1)")
    args = parser.parse_args()

    if args.build:
        asyncio.run(build())

    main()
