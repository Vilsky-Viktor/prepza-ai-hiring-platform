"""Tests the translation of prepza's own texts (news posts and campaign emails) on
datasets/translations.json: each source translated into each language by generation's own batch
request (sent at once, batch_direct.py) and checked as the service checks a reply, then checked
by code (limits, kept names and links, Markdown, paragraphs, script) and judged by
judges/translation.md. The judge is checked on traps planted by code in this run's
own translations (a statement left out, a number changed): it must catch every one.

    evals/run.sh generation translations_test.py --label base     # --repeat 2, --only n01,c02,
                                                                  # --languages de,ja, --sample 4

Costs about $0.40 for the translations and $0.80 for the judge at one repeat."""

import argparse
import asyncio
import json
import random
import re
import time

from batch_direct import run_direct
from common import (
    DATASETS,
    JUDGE_MODEL,
    RESULTS,
    cost,
    generation_models,
    judge,
    load,
    prompt,
    run_record,
    save,
)
from langchain_core.messages import HumanMessage
from prepza_common.config.constants import LANGUAGES
from pydantic import BaseModel, Field
from stats import share
from text_checks import in_script, keeps, paragraphs

from app.config.settings import settings
from app.constants.batch_work import BatchKind, BatchStep
from app.schemas.campaigns import CampaignSource
from app.schemas.news import NewsSource

SEED = 7
LINK = re.compile(r"\]\((\S+?)\)")


class TranslationReview(BaseModel):
    faithful: bool = Field(description="Says exactly what the source says")
    native: bool = Field(description="Reads as a native speaker in hiring would write it")
    one_language: bool = Field(description="Everything but names and links in the language")
    issue: str = Field(description="The main problem in a few words, or empty")


def fields_of(case: dict) -> dict:
    if case["kind_of"] == "news":
        return {"title": case["title"], "text": case["text"]}

    return {"subject": case["subject"], "text": case["text"], "button": case["button"] or ""}


async def translate(case: dict, language: str) -> dict:
    """The service's translation as its batch request asks for it (batch_direct.py) and what it
    used; `error` when it gave up (empty or too long every time)."""
    started = time.monotonic()
    kind = BatchKind.NEWS if case["kind_of"] == "news" else BatchKind.CAMPAIGN
    source = (
        NewsSource(title=case["title"], text=case["text"], missing=[language])
        if kind == BatchKind.NEWS
        else CampaignSource(
            subject=case["subject"], text=case["text"], button=case["button"], missing=[language]
        )
    )
    payload = {"source": source.model_dump(), "language": language}
    result, used = await run_direct(kind, BatchStep.TRANSLATE, payload)

    return {
        "fields": result.model_dump() if result else None,
        "error": None if result else "gave up",
        "cost": sum(cost(model.split("-20")[0], usage) for model, usage in used),
        "tokens": sum(u.get("input_tokens", 0) + u.get("output_tokens", 0) for _, u in used),
        "seconds": time.monotonic() - started,
    }


def code_checks(case: dict, language: str, fields: dict) -> dict:
    """What code can check of a translation: True for each check it passes."""
    text = fields["text"]
    whole = "\n".join(fields.values())
    source_numbers = [n for n in case.get("numbers", []) if re.search(r"\d", n)]
    digits = [re.sub(r"\D", "", n) for n in source_numbers]

    return {
        "script": in_script(whole, language, case["keep"]),
        "names": keeps(whole, case["keep"]),
        "prepza_lowercase": "Prepza" not in whole and "PREPZA" not in whole,
        "links": all(link in text for link in case.get("links", [])),
        "paragraphs": paragraphs(text) == paragraphs(case["text"]),
        "bold": text.count("**") == case["text"].count("**"),
        "numbers": all(
            d in re.sub(r"[^\d\n ]", "", whole.translate(ARABIC_DIGITS)) for d in digits
        ),
        "button": bool(fields.get("button")) == bool(case.get("button"))
        if case["kind_of"] == "campaign"
        else True,
        "no_quotes": not whole.strip().startswith(('"', "«", "„", "“")),
    }


# Arabic, Persian, Devanagari and Thai digits read as Western ones, for the number check.
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹०१२३४५६७८९๐๑๒๓๔๕๖๗๘๙", "0123456789" * 4)


def as_text(fields: dict) -> str:
    return "\n\n".join(f"<{name}>\n{value}\n</{name}>" for name, value in fields.items() if value)


async def review(case: dict, language: str, fields: dict) -> dict:
    text = prompt("translation").format(
        language=LANGUAGES[language], source=as_text(fields_of(case)), translation=as_text(fields)
    )
    result = (
        await judge()
        .with_structured_output(TranslationReview, include_raw=True)
        .ainvoke([HumanMessage(content=text)])
    )

    return {
        **result["parsed"].model_dump(),
        "judge_cost": cost(JUDGE_MODEL, result["raw"].usage_metadata or {}),
    }


def planted(fields: dict) -> list[tuple[str, dict]]:
    """Broken copies of a translation the judge must fail: its last sentence left out, and its
    first number changed (when it has one)."""
    traps = []
    text = fields["text"]
    sentences = re.split(r"(?<=[.!?。！？؟।])\s*", text.strip())
    sentences = [s for s in sentences if s.strip()]

    if len(sentences) > 1:
        traps.append(("left out", {**fields, "text": text.replace(sentences[-1], "").strip()}))

    number = re.search(r"\d+", text)

    if number:
        changed = str(int(number.group()) + 7)
        traps.append(("number", {**fields, "text": text.replace(number.group(), changed, 1)}))

    return traps


async def main(args) -> None:
    data = load(DATASETS / "translations.json")
    cases = [{**c, "kind_of": "news"} for c in data["news"]]
    cases += [{**c, "kind_of": "campaign"} for c in data["campaigns"]]
    cases = [c for c in cases if not args.only or c["id"] in args.only.split(",")]

    if args.sample:
        cases = random.Random(SEED).sample(cases, min(args.sample, len(cases)))

    languages = args.languages.split(",") if args.languages else data["languages"]
    models = generation_models(settings, ("translation",))
    limit = asyncio.Semaphore(6)

    async def one(case: dict, language: str, turn: int) -> dict:
        async with limit:
            found = await translate(case, language)
            row = {"id": case["id"], "language": language, "turn": turn, **found}

            if found["fields"] is None:
                return row

            row["checks"] = code_checks(case, language, found["fields"])
            row["review"] = await review(case, language, found["fields"])
            row["traps"] = [
                {"kind": kind, **await review(case, language, broken)}
                for kind, broken in planted(found["fields"])
            ]

            return row

    rows = await asyncio.gather(
        *(one(c, lang, turn) for c in cases for lang in languages for turn in range(args.repeat))
    )
    report(rows, models, args)


def report(rows: list[dict], models: str, args) -> None:
    done = [r for r in rows if r["fields"] is not None]
    passed = [r for r in done if all(r["checks"].values())]
    judged = [r["review"] for r in done]
    traps = [t for r in done for t in r["traps"]]
    failed_checks = {}

    for r in done:
        for name, ok in r["checks"].items():
            failed_checks[name] = failed_checks.get(name, 0) + (not ok)

    scores = {
        "translations": len(rows),
        "written": share(len(done), len(rows)),
        "code_checks": share(len(passed), len(rows)),
        "failed_checks": {name: n for name, n in failed_checks.items() if n},
        "faithful": share(sum(j["faithful"] for j in judged), len(rows)),
        "native": share(sum(j["native"] for j in judged), len(rows)),
        "one_language": share(sum(j["one_language"] for j in judged), len(rows)),
        "judge_traps_caught": f"{sum(not t['faithful'] for t in traps)} of {len(traps)}",
    }
    spent = {
        "translations": round(sum(r["cost"] for r in rows), 4),
        "judge": round(sum(r["review"]["judge_cost"] for r in done), 4)
        + round(sum(t["judge_cost"] for t in traps), 4),
    }
    seconds = sorted(r["seconds"] for r in rows)
    measured = {
        "tokens": sum(r["tokens"] for r in rows),
        "median_seconds": round(seconds[len(seconds) // 2], 1),
    }
    run = run_record(
        model=models, repeat=args.repeat, only=args.only, scores=scores, cost=spent, **measured
    )
    save(RESULTS / f"translations_{args.label}.json", {"run": run, "rows": rows})
    print(json.dumps({"scores": scores, "cost": spent, **measured}, indent=1, ensure_ascii=False))

    for r in rows:
        if r["fields"] is None:
            print(f"- {r['id']} {r['language']}: {r['error']}")
        elif not all(r["checks"].values()) or not (
            r["review"]["faithful"] and r["review"]["native"]
        ):
            bad = [name for name, ok in r["checks"].items() if not ok]
            print(f"- {r['id']} {r['language']}: {bad} {r['review']['issue']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    parser.add_argument("--only", default="")
    parser.add_argument("--languages", default="")
    parser.add_argument("--sample", type=int, default=0)
    parser.add_argument("--repeat", type=int, default=1)
    asyncio.run(main(parser.parse_args()))
