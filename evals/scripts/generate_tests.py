"""Generates whole tests from datasets/inputs.json through the real pipeline (extraction, topics,
every topic approved, questions, fill), and reports cost, time and tokens. Nothing is saved to a
library. Question reuse and the draft cache are off, so every run makes every call itself.

    evals/run.sh generation generate_tests.py python_backend senior_accountant
    MODEL=gpt-6-luna EFFORT=low evals/run.sh generation generate_tests.py --all --label luna
    OVERSAMPLE=1.0 evals/run.sh generation generate_tests.py python_backend --label oversample-1.0
    evals/run.sh generation generate_tests.py typescript_node --template --label t   # 90 a topic

Writes results/test_<domain>_<label>.json in the question format the other scripts read. At 70
questions a topic a test costs about $0.07-0.20 on gpt-6-luna at high, about $1.00 on
gpt-6.1-sol (7 topics)."""

import argparse
import asyncio
import os
import time
import uuid

from common import DATASETS, RESULTS, cost, generation_models, load, run_record, save
from langchain_core.callbacks import get_usage_metadata_callback
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from testee_common.ai.multi_answer import multi_share
from testee_common.limits.limits import limit

import generation.helpers.questions as question_helpers
import generation.services.graph as graph_module
import generation.services.nodes.fan_out as fan_out_node
import generation.services.top_up as top_up_module
from generation.config import settings
from generation.constants.generation import RECURSION_LIMIT
from generation.integrations.redis import get_redis
from generation.repositories import draft_cache


async def no_reuse(state):
    share = await multi_share(get_redis())

    return {"topic_embeddings": [], "reused": [[] for _ in state["topics"]], "multi_share": share}


async def no_cache(*_args):
    return None


def tune(fill_calls: list) -> None:
    """OVERSAMPLE replaces QUESTION_OVERSAMPLE everywhere it's read, and every call that tops up a
    short topic is counted: what a lower oversample saves, the fill-ups pay back, one at a time."""
    if "OVERSAMPLE" in os.environ:
        for module in (fan_out_node, question_helpers):
            module.QUESTION_OVERSAMPLE = float(os.environ["OVERSAMPLE"])

    generate_questions = top_up_module.generate_questions

    async def counted(task):
        fill_calls.append(task["topic"])

        return await generate_questions(task)

    top_up_module.generate_questions = counted


async def generate(domain: dict, fill_calls: list, template: bool) -> tuple[list[dict], dict]:
    graph = graph_module.build_graph(InMemorySaver())
    config = {
        "configurable": {"thread_id": str(uuid.uuid4())},
        "max_concurrency": await limit(get_redis(), "GENERATION_CALLS_AT_ONCE"),
        "recursion_limit": RECURSION_LIMIT,
    }
    started = time.monotonic()

    with get_usage_metadata_callback() as usage:
        await graph.ainvoke(
            {
                "input_text": domain["text"],
                "language": "en",
                "template": template,
            },
            config,
        )
        topics = (await graph.aget_state(config)).values["topics"]
        state = await graph.ainvoke(
            Command(resume={"selected": list(range(len(topics))), "instructions": ""}), config
        )

    items = [
        {
            "id": f"{domain['id']}-{ti}-{qi}",
            "domain": domain["id"],
            "level": state["level"],
            "topic": topic["topic"],
            "question": text,
            "options": options,
        }
        for ti, topic in enumerate(state.get("final") or [])
        for qi, (text, options) in enumerate(
            zip(topic["questions"], topic["answer_options"], strict=True)
        )
    ]
    totals = {"input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0, "cost": 0.0}

    for name, metadata in usage.usage_metadata.items():
        totals["input_tokens"] += metadata.get("input_tokens", 0)
        totals["output_tokens"] += metadata.get("output_tokens", 0)
        totals["reasoning_tokens"] += (metadata.get("output_token_details") or {}).get(
            "reasoning", 0
        )
        totals["cost"] += cost(name, metadata)

    run = {
        "domain": domain["id"],
        "level": state["level"],
        "topics": len(state.get("final") or []),
        "questions": len(items),
        "seconds": round(time.monotonic() - started),
        "fill_calls": len(fill_calls),
        **totals,
    }

    return items, run


async def main(domain_ids: list[str], label: str, template: bool) -> None:
    models = generation_models(settings)
    fill_calls = []
    tune(fill_calls)
    graph_module.find_reused = no_reuse
    draft_cache.get = no_cache
    draft_cache.put = no_cache
    domains = {domain["id"]: domain for domain in load(DATASETS / "inputs.json")["domains"]}

    for domain_id in domain_ids:
        fill_calls.clear()
        items, run = await generate(domains[domain_id], fill_calls, template)
        run = {**run_record(model=models), **run}
        run["oversample"] = fan_out_node.QUESTION_OVERSAMPLE
        save(RESULTS / f"test_{domain_id}_{label}.json", {"run": run, "items": items})
        print(
            f"{domain_id}: {run['topics']} topics, {run['questions']} questions, {run['seconds']}s, "
            f"${run['cost']:.3f} (${run['cost'] / max(run['topics'], 1):.4f} a topic), "
            f"{run['fill_calls']} fill-up calls",
            flush=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("domains", nargs="*", help="domain ids from datasets/inputs.json")
    parser.add_argument("--all", action="store_true", help="every domain")
    parser.add_argument("--label", default="run", help="names the result files")
    parser.add_argument("--template", action="store_true", help="a template's topic size")
    args = parser.parse_args()
    chosen = (
        [d["id"] for d in load(DATASETS / "inputs.json")["domains"]] if args.all else args.domains
    )
    asyncio.run(main(chosen, args.label, args.template))
