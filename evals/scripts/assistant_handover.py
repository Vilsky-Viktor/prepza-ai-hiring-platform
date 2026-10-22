"""Asks datasets/assistant_handover.json's questions while every service a tool calls fails (it
doesn't answer), with the handover (after HANDOVER_FAILURES failed calls the model is told to
stop retrying and link the contact page) and without it. Graded by code: the contact page
linked after a failed call (and not without one), calls that failed on prepza's side, and an
answer given (a text or an action's card).

    evals/run.sh assistant assistant_handover.py --label base        # --repeat 2

Costs about $0.10."""

import argparse
import asyncio
import json
import re
from types import SimpleNamespace

import httpx
from assistant_fixture import OWNER_NAME, Fixture
from assistant_turns import MODEL, ask
from common import DATASETS, RESULTS, load, run_record, save
from stats import mean, share

from app.services import chat, tool_calls

MARKDOWN_LINK = re.compile(r"\]\([^)]*\)")
# A turn that keeps retrying makes more failed calls than this.
MAX_FAILED_CALLS = 3


async def unavailable(*args, **kwargs):
    raise httpx.ConnectError("down")


def grade(answer: dict) -> dict:
    # Every call fails on prepza's side here: each one refused is a failed call (the panel's
    # updates and an action's card don't go through the failing services).
    failed = sum(1 for item in answer["tools"] if item["refused"])

    return {
        "contact": "contact" in answer["linked"],
        # Links come from show, under the answer; one written in the text is made up.
        "link_in_text": bool(MARKDOWN_LINK.search(answer["text"] or "")),
        "failed_calls": failed,
        "stopped": failed <= MAX_FAILED_CALLS,
        # A prepared action's card is an answer without text.
        "answered": bool(answer["text"] or answer["actions"]) and answer["error"] is None,
    }


def summary(grades: list[dict], answers: list[dict]) -> dict:
    failed = [g for g in grades if g["failed_calls"]]
    total = len(grades)

    return {
        "contact_linked_after_a_failure": share(sum(g["contact"] for g in failed), len(failed)),
        "contact_linked_without_one": share(
            sum(g["contact"] for g in grades if not g["failed_calls"]), total - len(failed)
        ),
        "no_link_in_text": share(sum(not g["link_in_text"] for g in grades), total),
        "stopped_retrying": share(sum(g["stopped"] for g in grades), total),
        "answered": share(sum(g["answered"] for g in grades), total),
        "failed_calls_per_turn": mean([g["failed_calls"] for g in grades]),
        "cost_per_turn": mean([a["cost"] for a in answers], 5),
    }


async def main(label: str, repeat: int) -> None:
    data = load(DATASETS / "assistant_handover.json")
    turns = [(q, n) for n in range(1, repeat + 1) for q in data["questions"]]
    fixture = Fixture()
    real_handover = chat.with_handover
    found = {}

    try:
        facts = await fixture.create(load(RESULTS / "assistant_templates.json"))
        company = facts["company"]["id"]
        tool_calls.services = SimpleNamespace(get=unavailable, send=unavailable)

        for variant in ("with", "without"):
            chat.with_handover = real_handover if variant == "with" else (lambda r, b, n: r)
            found[variant] = await asyncio.gather(
                *(
                    ask(
                        fixture.owner_token,
                        OWNER_NAME,
                        company,
                        q["message"],
                        {},
                        [],
                        q["language"],
                    )
                    for q, _ in turns
                )
            )
    finally:
        chat.with_handover = real_handover
        await fixture.delete()

    answers = {
        variant: {f"{q['id']}.{n}": a for (q, n), a in zip(turns, items, strict=True)}
        for variant, items in found.items()
    }
    grades = {v: {k: grade(a) for k, a in items.items()} for v, items in answers.items()}
    scores = {v: summary(list(grades[v].values()), list(answers[v].values())) for v in answers}
    spent = round(sum(a["cost"] for items in answers.values() for a in items.values()), 4)
    run = run_record(model=MODEL, scores=scores, repeat=repeat, cost=spent)
    save(
        RESULTS / f"assistant_handover_{label}.json",
        {"run": run, "answers": answers, "grades": grades},
    )
    print(json.dumps({"scores": scores, "cost": spent}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    parser.add_argument("--repeat", type=int, default=2)
    args = parser.parse_args()
    asyncio.run(main(args.label, args.repeat))
