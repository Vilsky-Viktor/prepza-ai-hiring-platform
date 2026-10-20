"""Do the site's guide articles help the assistant on hiring-advice questions without hurting
the others?

Asks datasets/assistant_guides.json's guide questions and its general questions (from
assistant_questions.json) in the assistant's container, on the page-context test's throwaway data
(assistant_fixture.py), with the guide tools (list_guides, get_guide) and without them (as
before them: no tools, no instruction), then has the judge compare each pair blind: guide
questions against the article that answers them (judges/assistant_guide.md), general ones as
the page-context test does (judges/assistant_pair.md).

    evals/run.sh library assistant_templates.py create
    evals/run.sh assistant guides.py --label base
    evals/run.sh library assistant_templates.py remove

Each question is asked `--repeat` times (2) in each variant; `--only q01,g07` asks only those.
"""

import argparse
import asyncio
import json
import random
import re
from contextlib import contextmanager

import httpx
from assistant_fixture import API, OWNER_NAME, Fixture
from assistant_turns import MODEL, ask, readable
from common import DATASETS, RESULTS, load, prompt, run_record, save
from page_context import PairReview, judge_general, page_of, reviewed, share
from pydantic import BaseModel, Field

from app.services import chat
from app.services.registry import tools

VARIANTS = ("without", "with")
GUIDE_TOOLS = {"list_guides", "get_guide"}


class GuideVerdict(BaseModel):
    correct: bool = Field(description="Agrees with the article; nothing contradicts or is made up")
    complete: bool = Field(description="Covers the main points of a right answer")
    issue: str = Field(description="The main problem in a few words, or empty")


class GuidePair(PairReview):
    a: GuideVerdict
    b: GuideVerdict


@contextmanager
def without_guides():
    """The service as it was before the guide tools, for this block."""
    saved = (chat.ASSISTANT_SYSTEM, chat.tools)
    pattern = r"- For hiring advice and best practice.*?\n(?=- Never invent)"
    old = re.sub(pattern, "", saved[0], flags=re.DOTALL)

    if old == saved[0]:
        raise ValueError("The guide instructions weren't found: update without_guides")

    chat.ASSISTANT_SYSTEM = old
    chat.tools = lambda: {name: tool for name, tool in tools().items() if name not in GUIDE_TOOLS}

    try:
        yield
    finally:
        chat.ASSISTANT_SYSTEM, chat.tools = saved


async def run_variant(items: list[dict], pages: dict, facts: dict, token: str) -> dict:
    limit = asyncio.Semaphore(6)

    async def one(item: dict) -> dict:
        async with limit:
            page, company = page_of(pages[item["page"]], facts)

            return await ask(token, OWNER_NAME, company, item["question"], page, [])

    answers = await asyncio.gather(*(one(item) for item in items))

    return {item["id"]: answer for item, answer in zip(items, answers, strict=True)}


async def judge_guide(item: dict, page: str, article: str, answers: dict) -> dict:
    """A blind pair against the article; which variant is A is drawn per question."""
    order = list(VARIANTS)
    random.Random(item["id"]).shuffle(order)
    text = prompt("assistant_guide").format(
        article=article,
        page=page,
        question=item["question"],
        expect=item["expect"],
        answer_a=readable(answers[order[0]]),
        answer_b=readable(answers[order[1]]),
    )
    review, spent = await reviewed(text, GuidePair)
    verdicts = {order[0]: review.a.model_dump(), order[1]: review.b.model_dump()}
    winner = "tie" if review.better == "tie" else order["AB".index(review.better)]

    return {"verdicts": verdicts, "better": winner, "judge_cost": spent}


def used_guide(answer: dict, slugs: list[str]) -> dict:
    """Whether the answer read a guide that answers it, and offered one as a link."""
    links = {link for block in answer["shown"] for link in block["links"]}

    return {
        "read": any(
            call["name"] == "get_guide" and call["arguments"].get("slug") in slugs
            for call in answer["tools"]
        ),
        "linked": any(f"/guides/{slug}" in links for slug in slugs),
    }


def summary(guide_items: list, general_items: list, reviews: dict, answers: dict) -> dict:
    found = {}

    for variant in VARIANTS:
        guide = [reviews["guide"][item["id"]]["verdicts"][variant] for item in guide_items]
        general = [reviews["general"][item["id"]]["verdicts"][variant] for item in general_items]
        uses = [used_guide(answers[variant][item["id"]], item["guides"]) for item in guide_items]
        general_tools = [
            any(call["name"] in GUIDE_TOOLS for call in answers[variant][item["id"]]["tools"])
            for item in general_items
        ]
        found[variant] = {
            "guide_correct": share([verdict["correct"] for verdict in guide]),
            "guide_complete": share([verdict["complete"] for verdict in guide]),
            "guide_read_right_one": share([use["read"] for use in uses]),
            "guide_linked": share([use["linked"] for use in uses]),
            "general_correct": share([verdict["correct"] for verdict in general]),
            "general_right_scope": share([verdict["right_scope"] for verdict in general]),
            "general_right_tools": share([verdict["right_tools"] for verdict in general]),
            "general_called_guide_tools": share(general_tools),
            "failed_turns": sum(
                1 for answer in answers[variant].values() if answer["error"] is not None
            ),
        }

    for part, items in (("guide", guide_items), ("general", general_items)):
        better = [reviews[part][item["id"]]["better"] for item in items]
        found[f"{part}_with_vs_without"] = {
            "wins": better.count("with"),
            "ties": better.count("tie"),
            "losses": better.count("without"),
        }

    return found


def repeated(items: list[dict], only: str, repeat: int) -> list[dict]:
    """Each chosen question `repeat` times, as q01.1, q01.2, ..."""
    chosen = [item for item in items if not only or item["id"] in only.split(",")]

    return [{**item, "id": f"{item['id']}.{n}"} for n in range(1, repeat + 1) for item in chosen]


async def main(label: str, only: str, repeat: int) -> None:
    data = load(DATASETS / "assistant_guides.json")
    page_data = load(DATASETS / "assistant_questions.json")
    pages = page_data["pages"]
    general = [item for item in page_data["general"] if item["id"] in data["general"]]
    guide_items = repeated(data["guide"], only, repeat)
    general_items = repeated(general, only, repeat)
    items = guide_items + general_items
    fixture = Fixture()
    answers = {}

    try:
        facts = await fixture.create(load(RESULTS / "assistant_templates.json"))

        with without_guides():
            answers["without"] = await run_variant(items, pages, facts, fixture.owner_token)

        token = await fixture.token(fixture.owner_email)
        answers["with"] = await run_variant(items, pages, facts, token)
    finally:
        await fixture.delete()

    async with httpx.AsyncClient() as http:
        slugs = {slug for item in guide_items for slug in item["guides"]}
        articles = {
            slug: (await http.get(f"{API}/rounds/help/guides/{slug}")).json()["body"]
            for slug in slugs
        }

    facts_text = json.dumps(facts, ensure_ascii=False, indent=1)
    limit = asyncio.Semaphore(8)

    async def guide_one(item):
        async with limit:
            pair = {variant: answers[variant][item["id"]] for variant in VARIANTS}
            page = pages[item["page"]]["describe"]

            article = "\n\n".join(articles[slug] for slug in item["guides"])

            return await judge_guide(item, page, article, pair)

    async def general_one(item):
        async with limit:
            pair = {variant: answers[variant][item["id"]] for variant in VARIANTS}
            page = pages[item["page"]]["describe"]

            return await judge_general(item, page, facts_text, pair)

    found = await asyncio.gather(*(guide_one(item) for item in guide_items))
    reviews = {"guide": {item["id"]: r for item, r in zip(guide_items, found, strict=True)}}
    found = await asyncio.gather(*(general_one(item) for item in general_items))
    reviews["general"] = {item["id"]: r for item, r in zip(general_items, found, strict=True)}
    spent = {
        variant: round(sum(answer["cost"] for answer in answers[variant].values()), 4)
        for variant in VARIANTS
    }
    judged = [review["judge_cost"] for part in reviews.values() for review in part.values()]
    scores = summary(guide_items, general_items, reviews, answers)
    spent = {"assistant": spent, "judge": round(sum(judged), 4)}
    result = {
        "run": run_record(model=MODEL, repeat=repeat, only=only, scores=scores, cost=spent),
        "summary": scores,
        "cost": spent,
        "facts": facts,
        "answers": answers,
        "reviews": reviews,
    }
    save(RESULTS / f"assistant_guides_{label}.json", result)
    print(json.dumps({"summary": result["summary"], "cost": result["cost"]}, indent=1))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    parser.add_argument("--only", default="")
    parser.add_argument("--repeat", type=int, default=2)
    args = parser.parse_args()
    asyncio.run(main(args.label, args.only, args.repeat))
