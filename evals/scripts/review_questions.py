"""Measures a set of questions, and has the judge review them with judges/question_review.md.

    evals/run.sh generation review_questions.py datasets/questions.json [--sample 40]
    evals/run.sh generation review_questions.py datasets/key_traps.json        # catch rate
    evals/run.sh generation review_questions.py datasets/flagged_traps.json    # flagged ones
    evals/run.sh generation review_questions.py datasets/multi_questions.json  # multi-answer
    evals/run.sh generation review_questions.py results/test_x.json --sample 40  # a new test
    evals/run.sh generation review_questions.py datasets/questions.json --save-reference
    JUDGE_MODEL=gpt-6-luna evals/run.sh generation review_questions.py datasets/questions.json \\
        --compare-reference                                                    # test a judge

Measurements cost nothing; a review costs about $0.004-0.005 per question with Sol at high
reasoning, the default judge (JUDGE_MODEL, JUDGE_EFFORT). The result records the run, the scores
with their 95% intervals and the judge's cost."""

import argparse
import asyncio
import random
import statistics
import time

from common import (
    DATASETS,
    EVALS,
    JUDGE_EFFORT,
    JUDGE_MODEL,
    RESULTS,
    correct_options,
    cost,
    is_multi,
    judge,
    load,
    options_text,
    prompt,
    question_items,
    reviews_of,
    run_record,
    save,
    tokens_of,
)
from flagged_labels import caught
from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from stats import mean, share


class Review(BaseModel):
    key_correct: bool = Field(
        description="The options marked correct are exactly the ones that are correct"
    )
    # Named for single-answer questions, where it means exactly one defensible option; for a
    # multi-answer one, every option is clearly right or clearly wrong.
    single_correct: bool = Field(description="The key can't be argued (see the prompt)")
    distractors: int = Field(ge=1, le=5, description="How tempting the wrong options are")
    clarity: int = Field(ge=1, le=5, description="How clear and unambiguous the question is")
    relevance: int = Field(ge=1, le=5, description="How useful it is at this level")
    seconds: int = Field(description="Seconds a capable candidate needs to read and answer it")
    issue: str = Field(description="The main problem in a few words, or empty")


def longest_is_correct(items: list[dict]) -> str:
    """How often the longest option is a correct one, and how often it would be if length gave
    nothing away: 25% with one correct option of four, the share of correct options with more."""
    longest = chance = 0

    for item in items:
        sizes = [len(option["answer"]) for option in item["options"]]
        longest += any(
            option["correct"]
            and len(option["answer"]) == max(sizes)
            and sizes.count(max(sizes)) == 1
            for option in item["options"]
        )
        chance += len(correct_options(item)) / len(item["options"])

    return f"{100 * longest / len(items):.0f}% (by chance {100 * chance / len(items):.0f}%)"


def measure(items: list[dict]) -> dict:
    """What can be counted without a judge; single- and multi-answer questions apart."""
    single = [item for item in items if not is_multi(item)]
    multi = [item for item in items if is_multi(item)]
    measured = {
        "questions": len(items),
        "multi_answer": len(multi),
        "question_chars": round(statistics.mean(len(item["question"]) for item in items)),
        "option_chars": round(
            statistics.mean(len(o["answer"]) for item in items for o in item["options"])
        ),
        "with_example": f"{100 * sum('```' in item['question'] for item in items) / len(items):.0f}%",
    }

    if single:
        # About 25% when the correct option's length gives nothing away.
        measured["correct_is_longest"] = longest_is_correct(single)

    if multi:
        measured["multi_correct_is_longest"] = longest_is_correct(multi)
        measured["multi_correct_counts"] = {
            n: sum(len(correct_options(item)) == n for item in multi) for n in (2, 3)
        }

    return measured


async def review(llm, item: dict) -> dict:
    text = prompt("question_review").format(
        level=item["level"],
        topic=item["topic"],
        question=item["question"],
        options=options_text(item),
    )
    result = await llm.ainvoke([HumanMessage(content=text)])
    spent = cost(JUDGE_MODEL, result["raw"].usage_metadata or {})

    return {"id": item["id"], **result["parsed"].model_dump(), "judge_cost": spent}


def summary(reviews: list[dict], items: dict[str, dict]) -> dict:
    """Shares and means with their 95% intervals (stats.py)."""
    counted = lambda rows, key: share(sum(r[key] for r in rows), len(rows))
    scored = lambda key: mean([r[key] for r in reviews])
    result = {
        "reviewed": len(reviews),
        "key_correct": counted(reviews, "key_correct"),
        "single_correct": counted(reviews, "single_correct"),
        "distractors": scored("distractors"),
        "clarity": scored("clarity"),
        "relevance": scored("relevance"),
    }

    # Each kind's key accuracy apart: multi-answer keys must reach the same target.
    for kind, rows in (
        ("single", [r for r in reviews if not is_multi(items[r["id"]])]),
        ("multi", [r for r in reviews if is_multi(items[r["id"]])]),
    ):
        if rows and len(rows) < len(reviews):
            result[f"{kind}_answer"] = {
                "reviewed": len(rows),
                "key_correct": counted(rows, "key_correct"),
                "unarguable_key": counted(rows, "single_correct"),
            }

    return result


def kappa(pairs: list[tuple[bool, bool]]) -> float:
    """Cohen's kappa of two judges' yes/no verdicts: agreement beyond what chance gives, which
    plain agreement hides when nearly every key is right."""
    seen = sum(a == b for a, b in pairs) / len(pairs)
    yes_a = sum(a for a, _ in pairs) / len(pairs)
    yes_b = sum(b for _, b in pairs) / len(pairs)
    chance = yes_a * yes_b + (1 - yes_a) * (1 - yes_b)

    return 1.0 if chance == 1 else round((seen - chance) / (1 - chance), 2)


def compare(reviews: list[dict], items: dict[str, dict]) -> dict:
    """Against what's known: the traps' expected keys, or the reference verdicts. Agreement with
    the reference is split by its verdict, as wrong keys are rare."""
    found = {}
    expected = [r for r in reviews if "expected_key_correct" in items[r["id"]]]

    if expected:
        right = sum(r["key_correct"] == items[r["id"]]["expected_key_correct"] for r in expected)
        found["traps_caught"] = f"{right} of {len(expected)}"

    # Flagged questions (flagged_traps.json): each flag's problem found, by flagged_labels.py.
    for flag in sorted({items[r["id"]]["flag"] for r in reviews if "flag" in items[r["id"]]}):
        rows = [r for r in reviews if items[r["id"]].get("flag") == flag]
        found[f"flagged_{flag}_caught"] = (
            f"{sum(caught(r, items[r['id']]) for r in rows)} of {len(rows)}"
        )

    reference_path = DATASETS / "reviews.json"
    reference = {r["id"]: r for r in reviews_of(reference_path)} if reference_path.exists() else {}
    shared = [r for r in reviews if r["id"] in reference]

    if shared:
        pairs = [(reference[r["id"]]["key_correct"], r["key_correct"]) for r in shared]
        right = [b for a, b in pairs if a]
        wrong = [not b for a, b in pairs if not a]
        found["reference_agreement"] = {
            "key": f"{sum(a == b for a, b in pairs)} of {len(pairs)}",
            "right_keys_kept": f"{sum(right)} of {len(right)}",
            "wrong_keys_found": f"{sum(wrong)} of {len(wrong)}",
            "kappa": kappa(pairs),
        }

    print(found)

    return found


async def main(
    path: str, sample: int | None, save_reference: bool, compare_reference: bool
) -> None:
    data = load(EVALS / path)
    items = question_items(EVALS / path)
    measured = measure(items)
    print("measured:", measured)
    chosen = random.Random(7).sample(items, sample) if sample and sample < len(items) else items
    llm = judge().with_structured_output(Review, include_raw=True)
    limit = asyncio.Semaphore(8)

    async def one(item):
        async with limit:
            return await review(llm, item)

    started = time.monotonic()

    with get_usage_metadata_callback() as usage:
        reviews = await asyncio.gather(*(one(item) for item in chosen))

    seconds = round(time.monotonic() - started)
    by_id = {item["id"]: item for item in items}
    scores = summary(reviews, by_id)
    spent = round(sum(r["judge_cost"] for r in reviews), 4)
    print(f"judged by {JUDGE_MODEL} ({JUDGE_EFFORT}), ${spent:.2f}:", scores)

    if compare_reference or any("expected_key_correct" in i or "flag" in i for i in chosen):
        scores["checks"] = compare(reviews, by_id)

    # How the questions were made (a dataset's model and date, a test's run), beside the review.
    made = {k: data[k] for k in ("model", "built", "run") if isinstance(data, dict) and k in data}
    run = run_record(
        questions=path,
        made=made,
        measured=measured,
        scores=scores,
        cost=spent,
        seconds=seconds,
        tokens=tokens_of(usage.usage_metadata),
    )
    name = path.replace("/", "_").removesuffix(".json")
    result = {"run": run, "reviews": reviews}
    save(RESULTS / f"reviews_{name}_{JUDGE_MODEL}_{JUDGE_EFFORT}.json", result)

    if save_reference:
        save(
            DATASETS / "reviews.json",
            {
                "about": f"Reference verdicts on {path} by {JUDGE_MODEL} ({JUDGE_EFFORT}).",
                "run": run,
                "reviews": reviews,
            },
        )

    for r in reviews:
        if not r["key_correct"] or not r["single_correct"]:
            print(f"- {r['id']}: {r['issue']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="a question file, relative to evals/")
    parser.add_argument("--sample", type=int)
    parser.add_argument("--save-reference", action="store_true")
    parser.add_argument("--compare-reference", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.path, args.sample, args.save_reference, args.compare_reference))
