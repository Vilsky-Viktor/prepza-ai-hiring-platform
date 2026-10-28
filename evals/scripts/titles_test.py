"""Tests the assistant's conversation titles on datasets/titles.json: each conversation goes
through the service's own title_prompt and write_title, its title through clean_title, then code
checks it (length before cutting, one line, nothing forbidden, the language's script) and
judges/title.md grades it. The judge is checked every run on traps made by code: another
conversation's title, and a generic one, must not pass.

    evals/run.sh assistant titles_test.py --label base     # --repeat 3, --only t01,t09, --sample 6

Costs about $0.01 for the titles and $0.30 for the judge at 3 repeats."""

import argparse
import asyncio
import json
import random
import re
import time
from itertools import pairwise

from common import DATASETS, JUDGE_MODEL, RESULTS, cost, judge, load, prompt, run_record, save
from langchain_core.messages import AIMessage, HumanMessage
from prepza_common.config.constants import LANGUAGES
from pydantic import BaseModel, Field
from stats import share
from text_checks import in_script

from assistant.config import settings
from assistant.constants.titles import MAX_TITLE_LENGTH
from assistant.helpers.titles import clean_title, title_prompt
from assistant.services.titles import write_title

PHONE = re.compile(r"\+?\d[\d ()-]{7,}\d")
EMAIL = re.compile(r"\S+@\S+")
GENERIC = "Conversation"
SEED = 7


class TitleReview(BaseModel):
    sums_up: bool = Field(description="Says what the whole conversation is about")
    right_language: bool = Field(description="Written in the language asked for")
    natural: bool = Field(description="Reads as a native speaker's short title")
    issue: str = Field(description="The main problem in a few words, or empty")


def chat_of(item: dict) -> list:
    kinds = {"human": HumanMessage, "ai": AIMessage}

    return [kinds[m["role"]](content=m["text"]) for m in item["messages"]]


async def write(item: dict) -> dict:
    started = time.monotonic()
    raw, usage = await write_title(title_prompt(chat_of(item), item["language"]))
    title = clean_title(raw)

    return {
        "raw": raw,
        "title": title,
        "cost": cost(settings.title_model, usage),
        "tokens": usage.get("total_tokens", 0),
        "seconds": time.monotonic() - started,
    }


def code_checks(item: dict, raw: str, title: str | None) -> dict:
    unclipped = raw.strip().strip("\"'“”«»„").rstrip(".").strip()

    return {
        "written": title is not None,
        "fits": len(unclipped) <= MAX_TITLE_LENGTH,
        "one_line": "\n" not in raw.strip(),
        "nothing_forbidden": not any(word in (title or "") for word in item["forbidden"]),
        "no_contact": not (EMAIL.search(title or "") or PHONE.search(title or "")),
        "script": in_script(title or "", item["language"], ["prepza", "Greenhouse", "Workable"]),
    }


async def review(item: dict, title: str) -> dict:
    conversation = "\n".join(f"{m['role']}: {m['text']}" for m in item["messages"])
    text = prompt("title").format(
        conversation=conversation,
        expect=item["expect"],
        language=LANGUAGES[item["language"]],
        title=title,
    )
    result = (
        await judge()
        .with_structured_output(TitleReview, include_raw=True)
        .ainvoke([HumanMessage(content=text)])
    )

    return {
        **result["parsed"].model_dump(),
        "judge_cost": cost(JUDGE_MODEL, result["raw"].usage_metadata or {}),
    }


async def main(args) -> None:
    items = load(DATASETS / "titles.json")["items"]
    items = [i for i in items if not args.only or i["id"] in args.only.split(",")]

    if args.sample:
        items = random.Random(SEED).sample(items, min(args.sample, len(items)))
    limit = asyncio.Semaphore(6)

    async def one(item: dict, turn: int) -> dict:
        async with limit:
            found = await write(item)
            row = {"id": item["id"], "turn": turn, **found}
            row["checks"] = code_checks(item, found["raw"], found["title"])
            row["review"] = await review(item, found["title"] or "") if found["title"] else None

            return row

    rows = await asyncio.gather(*(one(i, t) for i in items for t in range(args.repeat)))
    # Traps: each conversation judged with the next one's title, and with a generic one.
    english = [i for i in items if i["language"] == "en" and i["kind"] != "edge: a greeting only"]
    titles = {r["id"]: r["title"] for r in rows if r["turn"] == 0 and r["title"]}
    traps = [(i, titles[j["id"]]) for i, j in pairwise(english) if j["id"] in titles]
    traps += [(i, GENERIC) for i in english]
    trapped = await asyncio.gather(*(review(i, title) for i, title in traps))
    report(rows, trapped, args)


def report(rows: list[dict], trapped: list[dict], args) -> None:
    judged = [r["review"] for r in rows if r["review"]]
    clean = [r for r in rows if all(r["checks"].values())]
    failed = {}

    for r in rows:
        for name, ok in r["checks"].items():
            failed[name] = failed.get(name, 0) + (not ok)

    scores = {
        "titles": len(rows),
        "code_checks": share(len(clean), len(rows)),
        "failed_checks": {name: n for name, n in failed.items() if n},
        "sums_up": share(sum(j["sums_up"] for j in judged), len(rows)),
        "right_language": share(sum(j["right_language"] for j in judged), len(rows)),
        "natural": share(sum(j["natural"] for j in judged), len(rows)),
        "judge_traps_caught": f"{sum(not t['sums_up'] for t in trapped)} of {len(trapped)}",
    }
    spent = {
        "titles": round(sum(r["cost"] for r in rows), 4),
        "judge": round(sum(j["judge_cost"] for j in judged + trapped), 4),
    }
    seconds = sorted(r["seconds"] for r in rows)
    measured = {
        "tokens": sum(r["tokens"] for r in rows),
        "median_seconds": round(seconds[len(seconds) // 2], 1),
    }
    model = f"{settings.title_model} ({settings.title_reasoning_effort})"
    run = run_record(model=model, repeat=args.repeat, scores=scores, cost=spent, **measured)
    save(RESULTS / f"titles_{args.label}.json", {"run": run, "rows": rows})
    print(json.dumps({"scores": scores, "cost": spent, **measured}, indent=1, ensure_ascii=False))

    for r in rows:
        bad = [name for name, ok in r["checks"].items() if not ok]
        review = r["review"] or {}

        if bad or not (review.get("sums_up") and review.get("right_language")):
            print(f"- {r['id']} ({r['turn']}): {r['raw']!r} {bad} {review.get('issue', '')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    parser.add_argument("--only", default="")
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--sample", type=int, default=0, help="a fixed fast set of this many")
    asyncio.run(main(parser.parse_args()))
