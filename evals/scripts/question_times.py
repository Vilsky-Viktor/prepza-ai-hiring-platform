"""Fitted question times: rounds' estimate of how long each question takes
(rounds/helpers/question_times.py) against the judge's estimate of the seconds a capable candidate
needs to read and answer it (judges/question_review.md), frozen in datasets/question_times.json.
No measured answer times exist (local answers come from browser tests: 0-2 s or a time-out), so
the judge's estimate is the reference, and the judge's own noise is shown by a second run on 40.

    evals/run.sh rounds question_times.py                  # free: code only
    evals/run.sh rounds question_times.py --build \\
        datasets/questions.json=results/reviews_datasets_questions_gpt-6.1-sol_high.json ...

For each kind of question (level, single or multi-answer, with an example or not, language) it
reports how the estimate ranks questions against the judge (Spearman), and, over random draws of
DRAW questions at an average of AVERAGE seconds, how far each question's time lands from the time
the judge's estimates would give it: with fitted times and with equal times (weight 1). A kind
whose fitted times aren't closer than equal ones should get weight 1."""

import argparse
import random
import statistics
import time
from collections import defaultdict

from common import DATASETS, EVALS, RESULTS, is_multi, load, question_items, run_record, save
from stats import mean

from rounds.helpers.question_times import estimated_seconds, fitted, question_weight

NAME = "question_times.json"
SETS = ("questions.json", "multi_questions.json", "language_questions.json")
DRAW = 10
AVERAGE = 60
DRAWS = 3000


def build(pairs: list[str]) -> None:
    """The judge's seconds from review files, as `dataset=reviews` pairs; a pair whose dataset
    was already given adds its seconds as a second run (`retest`)."""
    items, runs = {}, []

    for pair in pairs:
        dataset, reviews = pair.split("=")
        data = load(EVALS / reviews)
        runs.append({"dataset": dataset, "reviews": reviews, **data["run"]})

        for review in data["reviews"]:
            key = (dataset, review["id"])
            field = "retest" if key in items else "seconds"
            items.setdefault(key, {"set": dataset.split("/")[-1], "id": review["id"]})
            items[key][field] = review["seconds"]

    save(
        DATASETS / NAME,
        {
            "about": "The judge's seconds to read and answer each question (made-up questions "
            "of the question sets); retest: a second run of the same judge.",
            "built": max(run["date"] for run in runs),
            "model": runs[0]["judge"],
            "runs": [{k: run.get(k) for k in ("dataset", "date", "judge", "cost")} for run in runs],
            "items": list(items.values()),
        },
    )


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    result = [0.0] * len(values)
    start = 0

    while start < len(order):
        end = start

        while end + 1 < len(order) and values[order[end + 1]] == values[order[start]]:
            end += 1

        for position in range(start, end + 1):
            result[order[position]] = (start + end) / 2

        start = end + 1

    return result


def spearman(first: list[float], second: list[float]) -> float:
    if len(first) < 3:
        return float("nan")

    a, b = ranks(first), ranks(second)
    mean_a, mean_b = statistics.mean(a), statistics.mean(b)
    top = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b, strict=True))
    bottom = (sum((x - mean_a) ** 2 for x in a) * sum((y - mean_b) ** 2 for y in b)) ** 0.5

    return round(top / bottom, 2) if bottom else float("nan")


def kind(item: dict) -> str:
    language = item.get("language", "en")
    shape = "multi" if is_multi(item) else "single"
    shown = "example" if "```" in item["question"] else "text"

    return f"{language} {item['level']} {shape} {shown}" if language == "en" else language


def draw_errors(rows: list[dict], rng: random.Random) -> dict[str, dict[str, list[float]]]:
    """Each drawn question's distance from its reference time, as a share of the average: with
    fitted times and with equal ones. Draws stay within one level and language, as an interview."""
    errors = defaultdict(lambda: {"fitted": [], "equal": []})
    groups = defaultdict(list)

    for row in rows:
        groups[(row["item"].get("language", "en"), row["item"]["level"])].append(row)

    for group in groups.values():
        if len(group) < DRAW:
            continue

        for _ in range(DRAWS // len(groups)):
            chosen = rng.sample(group, DRAW)
            ours = fitted([row["weight"] for row in chosen], AVERAGE)
            reference = fitted([row["judge"] for row in chosen], AVERAGE)

            for row, mine, right in zip(chosen, ours, reference, strict=True):
                errors[row["kind"]]["fitted"].append(abs(mine - right) / AVERAGE)
                errors[row["kind"]]["equal"].append(abs(AVERAGE - right) / AVERAGE)

    return errors


def report(rows: list[dict], errors: dict) -> dict:
    by_kind = defaultdict(list)

    for row in rows:
        by_kind[row["kind"]].append(row)

    found = {}

    for name, group in sorted(by_kind.items()):
        drawn = errors.get(name)
        found[name] = {
            "questions": len(group),
            "judge_median": statistics.median(row["judge"] for row in group),
            "estimate_median": round(statistics.median(row["estimate"] for row in group)),
            "spearman": spearman([r["estimate"] for r in group], [r["judge"] for r in group]),
        }

        if drawn:
            better = [e < q for e, q in zip(drawn["equal"], drawn["fitted"], strict=True)]
            found[name] |= {
                "error_fitted": mean(drawn["fitted"], 3),
                "error_equal": mean(drawn["equal"], 3),
                "equal_closer": f"{100 * sum(better) / len(better):.0f}%",
            }

    return found


def main() -> None:
    started = time.monotonic()
    questions = {
        (name, item["id"]): item for name in SETS for item in question_items(DATASETS / name)
    }
    rows = []

    for entry in load(DATASETS / NAME)["items"]:
        item = questions[(entry["set"], entry["id"])]
        question = {"text": item["question"], "options": item["options"]}
        rows.append(
            {
                "item": item,
                "kind": kind(item),
                "judge": entry["seconds"],
                "retest": entry.get("retest"),
                "estimate": estimated_seconds(question),
                "weight": question_weight(question),
            }
        )

    english = [row for row in rows if row["item"].get("language", "en") == "en"]
    retested = [row for row in rows if row["retest"] is not None]
    errors = draw_errors(rows, random.Random(7))
    every = {
        key: [e for kind_errors in errors.values() for e in kind_errors[key]]
        for key in ("fitted", "equal")
    }
    scores = {
        "judge_retest": {
            "questions": len(retested),
            "spearman": spearman([r["judge"] for r in retested], [r["retest"] for r in retested]),
            "mean_abs_seconds": mean([abs(r["judge"] - r["retest"]) for r in retested]),
        },
        "english_spearman": spearman(
            [r["estimate"] for r in english], [r["judge"] for r in english]
        ),
        "error_fitted": mean(every["fitted"], 3),
        "error_equal": mean(every["equal"], 3),
        "kinds": report(rows, errors),
    }
    print(scores)
    run = run_record(
        dataset=NAME,
        draw=DRAW,
        average=AVERAGE,
        scores=scores,
        cost=0,
        seconds=round(time.monotonic() - started),
    )
    save(RESULTS / NAME, {"run": run})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", nargs="+", help="dataset=reviews pairs, relative to evals/")
    args = parser.parse_args()

    if args.build:
        build(args.build)

    main()
