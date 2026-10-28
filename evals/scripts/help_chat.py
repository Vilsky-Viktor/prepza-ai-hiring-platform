"""Tests the help chat (the site's chat for visitors who aren't signed in) on
datasets/help_questions.json: each message asked as the service asks it (its own prompt, the
platform guide, the FAQ, prices and the page's guide) and answered by its own model, then checked
by code (the sign-in marker) and judged by judges/help_answer.md against the same information.

    evals/run.sh rounds help_chat.py --label base               # --repeat 3, --only h01,h10

The help model runs at effort "none" with a little temperature, so each message is asked
`--repeat` times. Costs about $0.01 for the answers and $0.30-0.60 for the judge (the
information comes first in its prompt, so it's cached after the first call)."""

import argparse
import asyncio
import json

from common import DATASETS, JUDGE_MODEL, RESULTS, cost, judge, load, prompt, run_record, save
from langchain_core.messages import HumanMessage
from prepza_common.config.constants import LANGUAGES
from pydantic import BaseModel, Field
from stats import share

from rounds.config import settings
from rounds.constants.help import HelpRole
from rounds.helpers.help import knowledge
from rounds.helpers.page_guides import guide_text, page_guide
from rounds.integrations import billing, llm
from rounds.integrations.redis import get_redis
from rounds.schemas.help import HelpMessage
from rounds.services.help import build_messages, guide_limits

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


async def answer(item: dict, catalog: dict | None) -> dict:
    message = HelpMessage(role=HelpRole.USER, content=item["question"])
    messages = await build_messages([message], item["language"], catalog, item["page"])
    result = await llm.get_help_llm().ainvoke(messages)

    return {"text": result.content, "cost": cost(settings.help_model, result.usage_metadata or {})}


async def review(item: dict, info: str, found: dict) -> dict:
    guide = page_guide(item["page"], "en") if item["page"] else None
    page = f"\n\n<page_guide>\n{guide_text(guide)}\n</page_guide>" if guide else ""
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


async def main(label: str, only: str, repeat: int) -> None:
    items = load(DATASETS / "help_questions.json")["questions"]
    items = [item for item in items if not only or item["id"] in only.split(",")]
    catalog = await billing.catalog()
    # The judge reads what the chat reads, in English (the FAQ in the page's language aside).
    info = knowledge("en", catalog, await guide_limits(get_redis()))
    limit = asyncio.Semaphore(6)

    async def one(item: dict, turn: int) -> dict:
        async with limit:
            found = await answer(item, catalog)

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
    run = run_record(model=model, repeat=repeat, only=only, scores=scores, cost=spent)
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
    args = parser.parse_args()
    asyncio.run(main(args.label, args.only, args.repeat))
