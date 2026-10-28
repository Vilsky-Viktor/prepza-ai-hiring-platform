"""Tests how generation plans a test, through its own nodes: the extraction (title, requirements,
level) of datasets/postings.json's postings and inputs.json's texts, the topics drafted from
it, and the topics revised on reviewers' instructions. Code checks limits, levels, kept-out
names and script; judges/extraction.md, topics.md and revision.md grade coverage and the rest.
The judges are checked every run on traps made by code from the run's own results (requirements
or a topic dropped, a revision that changed nothing): they must fail them.

    evals/run.sh generation planning_test.py --label base   # --repeat 2, --only x01,r01, --sample 4

The draft cache is skipped, so every call is made. Costs about $0.30 for the model and $1.00 for
the judges at 2 repeats."""

import argparse
import asyncio
import json
import random
import time

from common import (
    DATASETS,
    RESULTS,
    cost,
    generation_models,
    load,
    run_record,
    save,
)
from langchain_core.callbacks import get_usage_metadata_callback
from planning_judges import ExtractionReview, RevisionReview, TopicsReview, judged, traps
from prepza_common.config.constants import LANGUAGES
from stats import share
from text_checks import in_script

from generation.config import settings
from generation.constants.generation import MAX_TOPIC_NAME_LENGTH
from generation.repositories import draft_cache
from generation.services.nodes import extraction, topics
from generation.services.nodes.revision import revise_topics
from generation.services.topic_caps import topic_caps

SEED = 7


async def measured(call):
    """The node's result, its cost, tokens and seconds."""
    started = time.monotonic()

    with get_usage_metadata_callback() as usage:
        result = await call

    spent = sum(cost(m.split("-20")[0], u) for m, u in usage.usage_metadata.items())
    tokens = sum(u.get("total_tokens", 0) for u in usage.usage_metadata.values())

    return result, {"cost": spent, "tokens": tokens, "seconds": time.monotonic() - started}


def topics_ok(found: list[dict], caps: dict, language: str) -> dict:
    names = [t["main_topic"] for t in found] + [s for t in found for s in t["subtopics"]]

    return {
        "topics_within_cap": len(found) <= caps["max_topics"],
        "subtopics_within_cap": all(len(t["subtopics"]) <= caps["max_subtopics"] for t in found),
        "names_short": all(len(name) <= MAX_TOPIC_NAME_LENGTH for name in names),
        "topics_script": in_script(" ".join(names), language),
    }


async def plan(case: dict, caps: dict) -> dict:
    """Extraction then topics for one posting, checked and judged."""
    language = case.get("language", "en")
    state = {"input_text": case["text"], "language": language, "template": case["template"]}
    extracted, spent = await measured(extraction.extract_info(state))
    forbidden = case.get("forbidden", []) + (
        case.get("forbidden_in_template", []) if case["template"] else []
    )
    written = " ".join([extracted["title"], *extracted["requirements"]])
    checks = {
        "level": extracted["level"] == case["level"],
        "nothing_forbidden": not any(word.lower() in written.lower() for word in forbidden),
        "extraction_script": in_script(written, language, case.get("keep", [])),
    }
    template_note = (
        "This is a public template: the title and requirements must not name the company, its "
        "products or its internal tools; a generic description of them counts as covered."
    )
    review, judge_cost = await judged(
        ExtractionReview,
        "extraction",
        posting=case["text"],
        must_cover=", ".join(case.get("must_cover", [])) or "every item of the posting",
        extraction=json.dumps(extracted, ensure_ascii=False, indent=1),
        template_note=template_note if case["template"] else "",
        language=LANGUAGES[language],
    )
    state |= {"requirements": extracted["requirements"], "level": extracted["level"]}
    drafted, topic_spent = await measured(topics.generate_topics(state))
    checks |= topics_ok(drafted["topics"], caps, language)
    topic_review, topic_judge = await judged(
        TopicsReview,
        "topics",
        requirements="\n".join(f"- {r}" for r in extracted["requirements"]),
        topics=json.dumps(drafted["topics"], ensure_ascii=False, indent=1),
        language=LANGUAGES[language],
    )

    return {
        "id": case["id"],
        "extraction": extracted,
        "topics": drafted["topics"],
        "checks": checks,
        "review": review,
        "topic_review": topic_review,
        "cost": spent["cost"] + topic_spent["cost"],
        "tokens": spent["tokens"] + topic_spent["tokens"],
        "seconds": spent["seconds"] + topic_spent["seconds"],
        "judge_cost": judge_cost + topic_judge,
        "state": state | {"topics": drafted["topics"]},
    }


async def revise(revision: dict, planned: dict, caps: dict) -> dict:
    state = planned["state"] | {"feedback": revision["instructions"]}
    revised, spent = await measured(revise_topics(state))
    before = json.dumps(state["topics"], ensure_ascii=False, indent=1)
    review, judge_cost = await judged(
        RevisionReview,
        "revision",
        before=before,
        instructions=revision["instructions"],
        expect=revision["expect"],
        after=json.dumps(revised["topics"], ensure_ascii=False, indent=1),
    )

    return {
        "id": revision["id"],
        "topics": revised["topics"],
        "checks": topics_ok(revised["topics"], caps, state["language"]),
        "review": review,
        **spent,
        "judge_cost": judge_cost,
        "before": state["topics"],
    }


async def main(args) -> None:
    data = load(DATASETS / "postings.json")
    inputs = {d["id"]: d for d in load(DATASETS / "inputs.json")["domains"]}
    cases = {p["id"]: p for p in data["postings"]}
    cases |= {i: {**inputs[i], "template": False} for i in data["from_inputs"]}
    only = set(args.only.split(",")) if args.only else None
    chosen = [c for i, c in cases.items() if not only or i in only]

    if args.sample:
        chosen = random.Random(SEED).sample(chosen, min(args.sample, len(chosen)))
    # Every call is made: the draft cache would answer from an earlier run.
    draft_cache.get = lambda *a: asyncio.sleep(0)
    draft_cache.put = lambda *a: asyncio.sleep(0)
    caps = await topic_caps()
    plans = await asyncio.gather(*(plan(c, caps) for c in chosen for _ in range(args.repeat)))
    by_id = {p["id"]: p for p in plans}
    wanted = [r for r in data["revisions"] if r["from"] in by_id and (not only or r["id"] in only)]
    wanted = [r for r in wanted for _ in range(args.repeat)]
    revisions = await asyncio.gather(*(revise(r, by_id[r["from"]], caps) for r in wanted))
    revisions = [{**r, **w} for r, w in zip(revisions, wanted, strict=True)]
    caught, trap_cost = await traps(plans, [r for r in revisions if r["id"] != "r05"], cases)
    report(plans, revisions, caught, trap_cost, args)


def report(plans, revisions, caught, trap_cost, args) -> None:
    def rate(rows, key, field):
        return share(sum(r[key][field] for r in rows), len(rows))

    scores = {
        "plans": len(plans),
        "code_checks": share(sum(all(p["checks"].values()) for p in plans), len(plans)),
        "failed_checks": {
            name: sum(not p["checks"][name] for p in plans)
            for name in plans[0]["checks"]
            if any(not p["checks"][name] for p in plans)
        }
        if plans
        else {},
        "extraction_covered": rate(plans, "review", "covered"),
        "extraction_invented": rate(plans, "review", "invented"),
        "title_ok": rate(plans, "review", "title_ok"),
        "topics_covered": rate(plans, "topic_review", "covered"),
        "topics_testable": rate(plans, "topic_review", "testable"),
        "topics_coherent": rate(plans, "topic_review", "coherent"),
        "language_ok": share(
            sum(p["review"]["language_ok"] and p["topic_review"]["language_ok"] for p in plans),
            len(plans),
        ),
        "revisions_applied": rate(revisions, "review", "applied"),
        "revisions_kept": rate(revisions, "review", "kept"),
        "revision_checks": share(sum(all(r["checks"].values()) for r in revisions), len(revisions)),
        "judge_traps": caught,
    }
    rows = plans + revisions
    spent = {
        "model": round(sum(r["cost"] for r in rows), 4),
        "judge": round(sum(r["judge_cost"] for r in rows) + trap_cost, 4),
    }
    seconds = sorted(r["seconds"] for r in plans)
    measured_run = {
        "tokens": sum(r["tokens"] for r in rows),
        "median_seconds_a_plan": round(seconds[len(seconds) // 2], 1) if seconds else 0,
    }
    models = generation_models(settings)
    run = run_record(model=models, scores=scores, cost=spent, **measured_run)

    for p in plans:
        p.pop("state")

    save(
        RESULTS / f"planning_{args.label}.json",
        {"run": run, "plans": plans, "revisions": revisions},
    )
    print(
        json.dumps({"scores": scores, "cost": spent, **measured_run}, indent=1, ensure_ascii=False)
    )

    for p in plans:
        bad = [name for name, ok in p["checks"].items() if not ok]
        notes = p["review"]["missing"] + p["topic_review"]["missing"]

        if bad or notes or p["review"]["invented"]:
            print(f"- {p['id']}: {bad} invented={p['review']['invented']} missing={notes}")

    for r in revisions:
        if not (r["review"]["applied"] and r["review"]["kept"]):
            print(f"- {r['id']}: {r['review']['issue']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    parser.add_argument("--only", default="")
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--sample", type=int, default=0, help="a fixed fast set of this many")
    asyncio.run(main(parser.parse_args()))
