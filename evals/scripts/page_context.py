"""Does the page context help the assistant on page questions without hurting general ones?

Asks datasets/assistant_questions.json's questions in the assistant's container, on throwaway
data (assistant_fixture.py, from the test's own templates), with the page context and without
it (as before it), then has the judge compare them: general questions blind, in pairs
(judges/assistant_pair.md), page questions one by one (judges/assistant_page.md).

    evals/run.sh library assistant_templates.py create
    evals/run.sh assistant page_context.py --label base
    evals/run.sh library assistant_templates.py remove

Each question is asked `--repeat` times (3) in each variant; `--only g01,p06` asks only those. The assistant's model is the service's own (ASSISTANT_MODEL): about $0.25 a repeat for its
turns, and about $0.30 a repeat for the judge (Sol at high).
"""

import argparse
import asyncio
import json
import random
from typing import Literal

import httpx
from assistant_fixture import API, OWNER_NAME, Fixture
from assistant_turns import MODEL, PAGE_TOOL, ask, before_page_context, readable
from common import (
    DATASETS,
    JUDGE_MODEL,
    RESULTS,
    cost,
    judge,
    load,
    prompt,
    run_record,
    save,
)
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

VARIANTS = ("without", "with")


class Verdict(BaseModel):
    correct: bool = Field(description="True to the data and answers the question")
    right_scope: bool = Field(description="Read the question's scope as meant")
    right_tools: bool = Field(description="Its tool calls fit")
    issue: str = Field(description="The main problem in a few words, or empty")


class PairReview(BaseModel):
    a: Verdict
    b: Verdict
    better: Literal["A", "B", "tie"]


class PageReview(BaseModel):
    passed: bool = Field(description="Does what a right answer does")
    asked_back: bool = Field(description="Asked which page, interview, candidate or company")
    issue: str = Field(description="The main problem in a few words, or empty")


def page_of(spec: dict, facts: dict) -> tuple[dict, str | None]:
    """The page context the panel would send for a dataset's page, and the company picked."""
    interviews = facts["interviews"]
    ben = next(row for row in interviews[0]["candidates"] if row["name"] == "Ben Ortiz")
    ids = {
        "company": facts["company"]["id"],
        "interview0": interviews[0]["id"],
        "interview1": interviews[1]["id"],
        "ben": ben["id"],
    }
    page = {"key": spec["key"], "path": spec["path"].format(**ids) + spec.get("query", "")}
    company = ids["company"] if spec.get("company") else None

    if company:
        page["company_id"] = company

    if "interview" in spec:
        page["interview_id"] = interviews[spec["interview"]]["id"]

    if "candidate" in spec:
        page["candidate_id"] = ids[spec["candidate"]]

    return page, company


async def run_variant(variant: str, data: dict, facts: dict, token: str) -> dict:
    """Every question's answer in one variant, a few at a time."""
    limit = asyncio.Semaphore(6)

    async def one(item: dict) -> dict:
        async with limit:
            page, company = page_of(data["pages"][item["page"]], facts)
            earlier = []

            if "earlier" in item:
                first = item["earlier"]
                first_page, _ = page_of(data["pages"][first["page"]], facts)
                found = await ask(token, OWNER_NAME, company, first["question"], first_page, [])
                # Before the page context, earlier messages had no page.
                stored = first_page if variant == "with" else None
                earlier = [
                    {"role": "user", "content": first["question"], "page": stored},
                    {"role": "assistant", "content": found["text"]},
                ]

            language = item.get("language", "en")
            result = await ask(
                token, OWNER_NAME, company, item["question"], page, earlier, language
            )
            result["earlier"] = earlier

            return result

    items = data["general"] + data["page"]
    answers = await asyncio.gather(*(one(item) for item in items))

    return {item["id"]: answer for item, answer in zip(items, answers, strict=True)}


async def reviewed(text: str, schema) -> tuple[BaseModel, float]:
    llm = judge().with_structured_output(schema, include_raw=True)
    result = await llm.ainvoke([HumanMessage(content=text)])

    return result["parsed"], cost(JUDGE_MODEL, result["raw"].usage_metadata or {})


async def judge_general(item: dict, page: str, facts: str, answers: dict) -> dict:
    """A blind pair: which variant is A is drawn per question, the same every run."""
    order = list(VARIANTS)
    random.Random(item["id"]).shuffle(order)
    text = prompt("assistant_pair").format(
        facts=facts,
        page=page,
        question=item["question"],
        expect=item["expect"],
        answer_a=readable(answers[order[0]]),
        answer_b=readable(answers[order[1]]),
    )
    review, spent = await reviewed(text, PairReview)
    verdicts = {order[0]: review.a.model_dump(), order[1]: review.b.model_dump()}
    winner = "tie" if review.better == "tie" else order["AB".index(review.better)]

    return {"verdicts": verdicts, "better": winner, "judge_cost": spent}


async def judge_page(item: dict, data: dict, facts: str, guides: dict, answer: dict) -> dict:
    describe = data["pages"][item["page"]]["describe"]
    conversation = f'The user asked on {describe}: "{item["question"]}"'

    if answer["earlier"]:
        before = data["pages"][item["earlier"]["page"]]["describe"]
        conversation = (
            f'Earlier, on {before}, the user asked "{item["earlier"]["question"]}" and the '
            f"assistant answered:\n{answer['earlier'][1]['content']}\nThen the user moved to "
            f'{describe} and asked: "{item["question"]}"'
        )

    key = data["pages"][item["page"]]["key"]
    text = prompt("assistant_page").format(
        facts=facts,
        guide=guides.get(key, "(not needed)"),
        conversation=conversation,
        expect=item["expect"],
        answer=readable(answer),
    )
    review, spent = await reviewed(text, PageReview)
    called = any(
        call["name"] == PAGE_TOOL and call["arguments"].get("key") == key
        for call in answer["tools"]
    )

    return {**review.model_dump(), "guide_called": called, "judge_cost": spent}


def share(values: list[bool]) -> str:
    return f"{sum(values)}/{len(values)}"


def summary(data: dict, general: dict, pages: dict) -> dict:
    found = {}

    for variant in VARIANTS:
        verdicts = [general[item["id"]]["verdicts"][variant] for item in data["general"]]
        found[variant] = {
            "correct": share([verdict["correct"] for verdict in verdicts]),
            "right_scope": share([verdict["right_scope"] for verdict in verdicts]),
            "right_tools": share([verdict["right_tools"] for verdict in verdicts]),
            "page_passed": share([pages[variant][item["id"]]["passed"] for item in data["page"]]),
            "guide_called": share(
                [
                    pages[variant][item["id"]]["guide_called"]
                    for item in data["page"]
                    if item["kind"] == "guide"
                ]
            ),
        }

    better = [general[item["id"]]["better"] for item in data["general"]]
    found["with_vs_without"] = {
        "wins": better.count("with"),
        "ties": better.count("tie"),
        "losses": better.count("without"),
    }

    return found


async def main(label: str, only: str, repeat: int) -> None:
    data = load(DATASETS / "assistant_questions.json")

    for part in ("general", "page"):
        chosen = [item for item in data[part] if not only or item["id"] in only.split(",")]
        # Each question `repeat` times, as g01.1, g01.2, ...: one answer of a small model varies.
        data[part] = [
            {**item, "id": f"{item['id']}.{n}"} for n in range(1, repeat + 1) for item in chosen
        ]
    fixture = Fixture()
    answers = {}

    try:
        facts = await fixture.create(load(RESULTS / "assistant_templates.json"))

        with before_page_context():
            answers["without"] = await run_variant("without", data, facts, fixture.owner_token)

        token = await fixture.token(fixture.owner_email)
        answers["with"] = await run_variant("with", data, facts, token)
    finally:
        await fixture.delete()

    facts_text = json.dumps(facts, ensure_ascii=False, indent=1)
    keys = {data["pages"][item["page"]]["key"] for item in data["page"] if item["kind"] == "guide"}

    async with httpx.AsyncClient() as http:
        guides = {key: (await http.get(f"{API}/site/help/pages/{key}")).text for key in keys}

    limit = asyncio.Semaphore(8)

    async def general_one(item):
        async with limit:
            pair = {variant: answers[variant][item["id"]] for variant in VARIANTS}
            page = data["pages"][item["page"]]["describe"]

            return await judge_general(item, page, facts_text, pair)

    async def page_one(item, variant):
        async with limit:
            answer = answers[variant][item["id"]]

            return await judge_page(item, data, facts_text, guides, answer)

    general = await asyncio.gather(*(general_one(item) for item in data["general"]))
    general = {item["id"]: review for item, review in zip(data["general"], general, strict=True)}
    pages = {}

    for variant in VARIANTS:
        found = await asyncio.gather(*(page_one(item, variant) for item in data["page"]))
        pages[variant] = {
            item["id"]: review for item, review in zip(data["page"], found, strict=True)
        }

    spent = {
        variant: round(sum(answer["cost"] for answer in answers[variant].values()), 4)
        for variant in VARIANTS
    }
    judged = [review["judge_cost"] for review in general.values()]
    judged += [review["judge_cost"] for found in pages.values() for review in found.values()]
    scores = summary(data, general, pages)
    spent = {"assistant": spent, "judge": round(sum(judged), 4)}
    result = {
        "run": run_record(model=MODEL, repeat=repeat, only=only, scores=scores, cost=spent),
        "summary": scores,
        "cost": spent,
        "facts": facts,
        "answers": answers,
        "general": general,
        "pages": pages,
    }
    save(RESULTS / f"assistant_page_context_{label}.json", result)
    print(json.dumps({"summary": result["summary"], "cost": result["cost"]}, indent=1))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    # Some ids only ("g01,p06"), to try the script.
    parser.add_argument("--only", default="")
    parser.add_argument("--repeat", type=int, default=3)
    args = parser.parse_args()
    asyncio.run(main(args.label, args.only, args.repeat))
