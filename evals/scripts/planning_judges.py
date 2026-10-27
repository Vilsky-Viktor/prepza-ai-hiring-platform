"""The judges of planning_test.py (judges/extraction.md, topics.md, revision.md): what each
returns, how one is asked, and their traps made from a run's own results."""

import asyncio
import json

from common import JUDGE_MODEL, cost, judge, prompt
from langchain_core.messages import HumanMessage
from prepza_common.config.constants import LANGUAGES
from pydantic import BaseModel, Field


class ExtractionReview(BaseModel):
    covered: bool = Field(description="Every testable item is among the requirements")
    missing: list[str] = Field(description="Items missing, a few words each")
    invented: bool = Field(description="Something the posting doesn't say")
    title_ok: bool = Field(description="The title names the role briefly")
    language_ok: bool = Field(description="Everything in the language asked for")


class TopicsReview(BaseModel):
    covered: bool = Field(description="Every requirement's skill has a subtopic")
    missing: list[str] = Field(description="Requirements left out")
    testable: bool = Field(description="Subtopics are testable knowledge")
    coherent: bool = Field(description="Each topic covers one subject")
    language_ok: bool = Field(description="Every name in the language asked for")


class RevisionReview(BaseModel):
    applied: bool = Field(description="Does what a right result does")
    kept: bool = Field(description="Nothing untouched was lost")
    issue: str = Field(description="The main problem, or empty")


async def judged(schema, name: str, **fields) -> tuple[dict, float]:
    result = (
        await judge()
        .with_structured_output(schema, include_raw=True)
        .ainvoke([HumanMessage(content=prompt(name).format(**fields))])
    )

    return result["parsed"].model_dump(), cost(JUDGE_MODEL, result["raw"].usage_metadata or {})


async def traps(plans: list[dict], revisions: list[dict], cases: dict) -> tuple[dict, float]:
    """The judges on broken copies of this run's results, each a failure: most requirements or
    half the topics left out, a revision that changed nothing."""
    jobs = []

    for p in plans:
        # Two thirds of the requirements, and half the topics, left out: clearly not covered.
        kept = p["extraction"]["requirements"][: len(p["extraction"]["requirements"]) // 3]
        extracted = {**p["extraction"], "requirements": kept}
        jobs.append(
            judged(
                ExtractionReview,
                "extraction",
                posting=cases[p["id"]]["text"],
                must_cover="every item of the posting",
                extraction=json.dumps(extracted, ensure_ascii=False),
                template_note="",
                language=LANGUAGES[cases[p["id"]].get("language", "en")],
            )
        )
        jobs.append(
            judged(
                TopicsReview,
                "topics",
                requirements="\n".join(f"- {r}" for r in p["extraction"]["requirements"]),
                topics=json.dumps(p["topics"][: len(p["topics"]) // 2], ensure_ascii=False),
                language=LANGUAGES[cases[p["id"]].get("language", "en")],
            )
        )

    for r in revisions:
        jobs.append(
            judged(
                RevisionReview,
                "revision",
                before=json.dumps(r["before"], ensure_ascii=False),
                instructions=r["instructions"],
                expect=r["expect"],
                after=json.dumps(r["before"], ensure_ascii=False),
            )
        )

    results = await asyncio.gather(*jobs)
    failed = [not (v.get("covered", True) and v.get("applied", True)) for v, _ in results]

    return {"caught": f"{sum(failed)} of {len(failed)}"}, sum(c for _, c in results)
