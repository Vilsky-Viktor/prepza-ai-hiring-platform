"""Counts, without a judge, how questions use examples and how long they take to read: per
domain (and its level), the share with an example (single- and multi-answer apart, and per
topic), the example's language tags ("text" ones that hold code counted apart), the example's
lines and characters, the whole question's characters (question, example and options) and its
estimated reading time against the one-minute rule (generation's prompts/question_rules.py).
With --reviews, the judge's scores per domain too, and its estimate of the seconds a capable
candidate needs to read and answer (median, share over 60 and over 90 seconds).

    evals/run.sh generation measure_examples.py results/questions_x.json \\
        --reviews results/reviews_results_questions_x_gpt-6.1-sol_high.json
    python3 evals/scripts/measure_examples.py results/test_python_backend_x.json   # free, local

Results files of generate_tests.py measure per topic, the way a template's topics are held."""

import argparse
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

EVALS = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"```([\w+-]*)\n(.*?)\n?```", re.DOTALL)
# What a "text" block holding code shows: a program's statements, an import, a file's JSON.
CODE_SIGNS = re.compile(
    r"=>|;\s*$|\{\s*$|^\s*(import|export|const|let|function|def|class|return|from)\b|"
    r"require\(|console\.|print\(|\"\w+\":",
    re.MULTILINE,
)
# Reading speed for the estimate: prose at 200 words a minute, an example's words slower.
PROSE_WPM = 200
EXAMPLE_WPM = 120


def is_multi(item: dict) -> bool:
    return sum(option["correct"] for option in item["options"]) > 1


def example(item: dict) -> tuple[str, str] | None:
    found = FENCE.search(item["question"])

    return (found.group(1), found.group(2)) if found else None


def reading_seconds(item: dict) -> float:
    shown = example(item)
    prose = FENCE.sub("", item["question"]) + " " + " ".join(o["answer"] for o in item["options"])
    seconds = 60 * len(prose.split()) / PROSE_WPM

    return seconds + (60 * len(shown[1].split()) / EXAMPLE_WPM if shown else 0)


def share(part: int, whole: int) -> str:
    return f"{part}/{whole} ({100 * part / whole:.0f}%)" if whole else "-"


def p90(values: list[float]) -> float:
    return sorted(values)[int(0.9 * (len(values) - 1))] if values else 0


def measure(items: list[dict]) -> dict:
    single = [item for item in items if not is_multi(item)]
    multi = [item for item in items if is_multi(item)]
    shown = [example(item) for item in items if example(item)]
    lines = [len(body.splitlines()) for _, body in shown]
    totals = [
        len(item["question"]) + sum(len(o["answer"]) for o in item["options"]) for item in items
    ]
    seconds = [reading_seconds(item) for item in items]
    languages = Counter(language or "(none)" for language, _ in shown)
    code_as_text = sum(
        1 for language, body in shown if language in ("text", "") and CODE_SIGNS.search(body)
    )

    return {
        "questions": len(items),
        "with_example": share(len(shown), len(items)),
        "single_with_example": share(sum(bool(example(i)) for i in single), len(single)),
        "multi_with_example": share(sum(bool(example(i)) for i in multi), len(multi)),
        "languages": dict(languages.most_common()),
        "code_tagged_text": code_as_text,
        "example_lines": f"mean {statistics.mean(lines):.1f}, p90 {p90(lines)}, max {max(lines)}"
        if lines
        else "-",
        "examples_over_8_lines": sum(count > 8 for count in lines),
        "example_chars": round(statistics.mean(len(body) for _, body in shown)) if shown else 0,
        "question_chars_without_example": round(
            statistics.mean(len(FENCE.sub("", item["question"])) for item in items)
        ),
        "total_chars": f"mean {statistics.mean(totals):.0f}, p90 {p90(totals)}",
        "reading_seconds": f"mean {statistics.mean(seconds):.0f}, p90 {p90(seconds):.0f}",
        "over_60_seconds": share(sum(s > 60 for s in seconds), len(items)),
    }


def timed(rows: list[dict]) -> str:
    """The judge's seconds to read and answer: median, 90th percentile, max, and how many go
    over 60, 75 and 90."""
    seconds = [r["seconds"] for r in rows]
    over = ", ".join(
        f"over {limit} {share(sum(s > limit for s in seconds), len(seconds))}"
        for limit in (60, 75, 90)
    )

    return (
        f"median {statistics.median(seconds):.0f}, p90 {p90(seconds)}, max {max(seconds)}, {over}"
    )


def judged(reviews: list[dict]) -> dict:
    mean = lambda key: round(statistics.mean(r[key] for r in reviews), 2)
    kinds = {
        kind: [r for r in reviews if r["multi"] == (kind == "multi")]
        for kind in ("single", "multi")
    }

    return {
        "reviewed": len(reviews),
        "answer_seconds": timed(reviews) if "seconds" in reviews[0] else "-",
        **{
            f"{kind}_answer_seconds": timed(rows)
            for kind, rows in kinds.items()
            if rows and "seconds" in rows[0]
        },
        "clarity": mean("clarity"),
        "relevance": mean("relevance"),
        "distractors": mean("distractors"),
        **{
            f"{kind}_key_correct": share(sum(r["key_correct"] for r in rows), len(rows))
            for kind, rows in kinds.items()
            if rows
        },
    }


def main(path: str, reviews_path: str | None, per_topic: bool) -> None:
    data = json.loads((EVALS / path).read_text())
    items = data["items"] if isinstance(data, dict) else data
    by_domain = defaultdict(list)

    for item in items:
        by_domain[(item["domain"], item["level"])].append(item)

    reviews = defaultdict(list)

    if reviews_path:
        by_id = {item["id"]: item for item in items}
        data = json.loads((EVALS / reviews_path).read_text())

        # A list, or {"run", "reviews"} as review_questions.py saves.
        for review in data["reviews"] if isinstance(data, dict) else data:
            item = by_id[review["id"]]
            reviews[(item["domain"], item["level"])].append({**review, "multi": is_multi(item)})

    report = {"all": measure(items)}

    if reviews:
        everything = [r for rows in reviews.values() for r in rows]
        report["all"]["judge"] = judged(everything)

        if "seconds" in everything[0]:
            # The time to read and answer by level and kind, for the timer's default per level.
            report["seconds_by_level"] = {
                f"{level} {kind}": timed(rows)
                for level in ("basic", "medium", "hard")
                for kind in ("single", "multi")
                if (
                    rows := [
                        r
                        for (_, lvl), group in reviews.items()
                        if lvl == level
                        for r in group
                        if r["multi"] == (kind == "multi")
                    ]
                )
            }

    for (domain, level), rows in sorted(by_domain.items()):
        key = f"{domain} ({level})"
        report[key] = measure(rows)

        if reviews[(domain, level)]:
            report[key]["judge"] = judged(reviews[(domain, level)])

        if per_topic:
            topics = defaultdict(list)

            for item in rows:
                topics[item["topic"]].append(item)

            report[key]["topics"] = {
                topic: {
                    "with_example": share(sum(bool(example(i)) for i in group), len(group)),
                    "multi": sum(is_multi(i) for i in group),
                }
                for topic, group in topics.items()
            }

    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="a question file, relative to evals/")
    parser.add_argument("--reviews", help="the judge's reviews of it, relative to evals/")
    parser.add_argument("--per-topic", action="store_true")
    args = parser.parse_args()
    main(args.path, args.reviews, args.per_topic)
