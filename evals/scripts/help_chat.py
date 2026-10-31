"""Tests the help chat (the site's chat for visitors who aren't signed in) on
datasets/help_questions.json: each message asked as the service asks it (its own prompt, the
platform guide, the FAQ, prices and the page's guide) and answered by its own model, then checked
by code (the sign-in marker) and judged by judges/help_answer.md against the same information.
The help chat is the assistant's; what it answers from comes from site, as in the service.

    evals/run.sh assistant help_chat.py --label base            # --repeat 3, --only h01,h10
    evals/run.sh assistant help_chat.py --dataset help_feedback.json --label feedback

The help model runs at effort "none" with a little temperature, so each message is asked
`--repeat` times. Costs about $0.01 for the answers and $0.30-0.60 for the judge (the
information comes first in its prompt, so it's cached after the first call)."""

import argparse
import asyncio
import json

from common import DATASETS, JUDGE_MODEL, RESULTS, cost, judge, load, prompt, run_record, save
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from stats import share
from testee_common.config.constants import LANGUAGES

from assistant.config import settings
from assistant.constants.help_chat import HelpRole
from assistant.integrations import llm
from assistant.integrations.help_knowledge import help_knowledge
from assistant.schemas.help_chat import HelpMessage
from assistant.services.help_chat import build_messages

SIGN_IN = "[[sign_in"


class HelpReview(BaseModel):
    passed: bool = Field(description="It does what a right answer does, in the right language")
    made_up: bool = Field(description="It states something the information doesn't support")
    issue: str = Field(description="The main problem in a few words, or empty")


def marker_ok(item: dict, answer: str) -> bool:
    """The sign-in marker: the expected one first, none when none is expected."""
    if item["sign_in"] == "any":
        return True

    if item["sign_in"] is None:
        return SIGN_IN not in answer

    return answer.lstrip().startswith(item["sign_in"])


def passed(rows: list[dict]) -> int:
    return sum(r["passed"] and r["marker_ok"] for r in rows)


async def answer(item: dict) -> dict:
    message = HelpMessage(role=HelpRole.USER, content=item["question"])
    known = await help_knowledge(None, item["page"])
    messages = build_messages([message], item["language"], known, item["page"])
    result = await llm.get_help_llm().ainvoke(messages)

    return {"text": result.content, "cost": cost(settings.help_model, result.usage_metadata or {})}


async def review(item: dict, info: str, found: dict) -> dict:
    guide = (await help_knowledge(None, item["page"])).page_guide if item["page"] else None
    page = f"\n\n<page_guide>\n{guide}\n</page_guide>" if guide else ""
    text = prompt("help_answer").format(
        knowledge=info + page,
        page=item["page"] or "unknown",
        language=LANGUAGES[item["language"]],
        question=item["question"],
        expect=item["expect"],
        answer=found["text"],
    )
    result = (
        await judge()
        .with_structured_output(HelpReview, include_raw=True)
        .ainvoke([HumanMessage(content=text)])
    )
    spent = cost(JUDGE_MODEL, result["raw"].usage_metadata or {})

    return {
        **result["parsed"].model_dump(),
        "marker_ok": marker_ok(item, found["text"]),
        "judge_cost": spent,
    }


async def main(label: str, only: str, repeat: int, dataset: str) -> None:
    items = load(DATASETS / dataset)["questions"]
    items = [item for item in items if not only or item["id"] in only.split(",")]
    # The judge reads what the chat reads, in English (the FAQ in the page's language aside).
    info = (await help_knowledge(None, None)).knowledge
    limit = asyncio.Semaphore(6)

    async def one(item: dict, turn: int) -> dict:
        async with limit:
            found = await answer(item)

            return {"id": item["id"], "turn": turn, **found, **await review(item, info, found)}

    rows = await asyncio.gather(*(one(item, turn) for item in items for turn in range(repeat)))
    kinds = sorted({item["kind"] for item in items})
    kind_of = {item["id"]: item["kind"] for item in items}
    scores = {
        "answers": len(rows),
        "passed": share(passed(rows), len(rows)),
        "made_up": share(sum(r["made_up"] for r in rows), len(rows)),
        "marker_ok": share(sum(r["marker_ok"] for r in rows), len(rows)),
        "by_kind": {
            kind: f"{passed([r for r in rows if kind_of[r['id']] == kind])} of "
            f"{sum(kind_of[r['id']] == kind for r in rows)}"
            for kind in kinds
        },
    }
    spent = {
        "help": round(sum(r["cost"] for r in rows), 4),
        "judge": round(sum(r["judge_cost"] for r in rows), 4),
    }
    model = f"{settings.help_model} ({settings.help_reasoning_effort})"
    run = run_record(
        model=model, dataset=dataset, repeat=repeat, only=only, scores=scores, cost=spent
    )
    save(RESULTS / f"help_chat_{label}.json", {"run": run, "answers": rows})
    print(json.dumps({"scores": scores, "cost": spent}, indent=1, ensure_ascii=False))

    for r in rows:
        if not (r["passed"] and r["marker_ok"]) or r["made_up"]:
            print(f"- {r['id']} ({r['turn']}): {r['issue'] or 'sign-in marker'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    parser.add_argument("--only", default="")
    parser.add_argument("--repeat", type=int, default=3)
    # The feedback cases (help_feedback.json) are kept apart from the hand-written ones.
    parser.add_argument("--dataset", default="help_questions.json")
    args = parser.parse_args()
    asyncio.run(main(args.label, args.only, args.repeat, args.dataset))
