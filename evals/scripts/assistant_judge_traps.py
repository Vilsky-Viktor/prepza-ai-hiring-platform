"""Checks the assistant's three judges (judges/assistant_pair.md, assistant_page.md,
assistant_guide.md) before their scores count, on traps with known verdicts made from a
page-context run's and a guides run's own answers: an answer a judge passed, against a broken
copy of it (its numbers changed, a made-up promise added, or asking back which interview is
meant), which it must fail (and rank lower in a pair); and the answer itself, which it must still
pass. Each judge is asked exactly as page_context.py and guides.py ask it. Reports traps caught
(true positives), answers kept (true negatives) and Cohen's kappa.

    evals/run.sh assistant assistant_judge_traps.py results/assistant_page_context_p1.json \\
        results/assistant_guides_g1.json --label base        # --per-judge 8

Costs about $0.30."""

import argparse
import asyncio
import json
import random
import re

import httpx
from assistant_fixture import API
from common import DATASETS, EVALS, JUDGE_MODEL, RESULTS, load, run_record, save
from guides import judge_guide
from page_context import judge_general, judge_page
from stats import share

SEED = 7
# What the judges' calls cost, added up as they're made.
SPENT = []
ASK_BACK = "Which interview do you mean? Please tell me its name."
MADE_UP = " prepza also guarantees every hire for 12 months and refunds a bad one in full."


def changed_numbers(text: str) -> str:
    """The text with every number moved, so each figure it states is wrong."""
    return re.sub(r"\d+", lambda m: str(int(m.group()) + 17), text)


def kappa(pairs: list[tuple[bool, bool]]) -> float:
    """Cohen's kappa of (expected, judged) verdicts, True meaning "a failed answer"."""
    total = len(pairs)
    agree = sum(e == j for e, j in pairs) / total
    yes_e = sum(e for e, _ in pairs) / total
    yes_j = sum(j for _, j in pairs) / total
    chance = yes_e * yes_j + (1 - yes_e) * (1 - yes_j)

    return round((agree - chance) / (1 - chance), 2) if chance < 1 else 1.0


def from_pair(review: dict) -> list[tuple[bool, bool]]:
    """A pair of the good answer ("with") and its broken copy ("without"): the copy must be
    judged wrong and ranked lower, the good one kept correct."""
    caught = not review["verdicts"]["without"]["correct"] and review["better"] == "with"

    return [(True, caught), (False, not review["verdicts"]["with"]["correct"])]


def picked(keys: list[str], limit: int, rng: random.Random) -> list[str]:
    return rng.sample(sorted(keys), min(limit, len(keys)))


async def pair_traps(run: dict, data: dict, limit: int, rng) -> list:
    """The pair judge: a general answer it passed, against its copy with every number moved."""
    facts = json.dumps(run["facts"], ensure_ascii=False, indent=1)
    items = {row["id"]: row for row in data["general"]}
    passed = [
        key
        for key, review in run["general"].items()
        if review["verdicts"]["with"]["correct"]
        and re.search(r"\d", run["answers"]["with"][key]["text"] or "")
    ]
    found = []

    for key in picked(passed, limit, rng):
        good = run["answers"]["with"][key]
        item = items[key.split(".")[0]]
        bad = {**good, "text": changed_numbers(good["text"])}
        page = data["pages"][item["page"]]["describe"]
        review = await judge_general(item, page, facts, {"with": good, "without": bad})
        SPENT.append(review["judge_cost"])
        found += from_pair(review)

    return found


async def page_traps(run: dict, data: dict, limit: int, rng) -> list:
    """The page judge: a page answer it passed, and the same turn asking back instead."""
    facts = json.dumps(run["facts"], ensure_ascii=False, indent=1)
    items = {row["id"]: row for row in data["page"]}
    passed = [key for key, review in run["pages"]["with"].items() if review["passed"]]
    chosen = picked(passed, limit, rng)
    keys = {data["pages"][items[key.split(".")[0]]["page"]]["key"] for key in chosen}

    async with httpx.AsyncClient(timeout=60) as http:
        guides = {key: (await http.get(f"{API}/site/help/pages/{key}")).text for key in keys}

    found = []

    for key in chosen:
        good = run["answers"]["with"][key]
        item = items[key.split(".")[0]]

        for answer, broken in ((good, False), ({**good, "text": ASK_BACK}, True)):
            review = await judge_page(item, data, facts, guides, answer)
            SPENT.append(review["judge_cost"])
            found.append((broken, not review["passed"]))

    return found


async def guide_traps(run: dict, data: dict, pages: dict, limit: int, rng) -> list:
    """The guide judge: a guide answer it found correct, against it with a made-up promise."""
    items = {row["id"]: row for row in data["guide"]}
    reviews = run["reviews"]["guide"]
    correct = [key for key, review in reviews.items() if review["verdicts"]["with"]["correct"]]
    chosen = picked(correct, limit, rng)
    slugs = {slug for key in chosen for slug in items[key.split(".")[0]]["guides"]}

    async with httpx.AsyncClient(timeout=60) as http:
        articles = {
            slug: (await http.get(f"{API}/site/help/guides/{slug}")).json()["body"]
            for slug in slugs
        }

    found = []

    for key in chosen:
        good = run["answers"]["with"][key]
        item = items[key.split(".")[0]]
        article = "\n\n".join(articles[slug] for slug in item["guides"])
        bad = {**good, "text": (good["text"] or "") + MADE_UP}
        page = pages[item["page"]]["describe"]
        review = await judge_guide(item, page, article, {"with": good, "without": bad})
        SPENT.append(review["judge_cost"])
        found += from_pair(review)

    return found


async def main(page_path: str, guides_path: str, label: str, per_judge: int) -> None:
    rng = random.Random(SEED)
    page_run = load(EVALS / page_path)
    guide_run = load(EVALS / guides_path)
    data = load(DATASETS / "assistant_questions.json")
    guide_data = load(DATASETS / "assistant_guides.json")
    found = {
        "pair": await pair_traps(page_run, data, per_judge, rng),
        "page": await page_traps(page_run, data, per_judge, rng),
        "guide": await guide_traps(guide_run, guide_data, data["pages"], per_judge, rng),
    }
    scores = {}

    for name, verdicts in found.items():
        traps = [judged for broken, judged in verdicts if broken]
        kept = [not judged for broken, judged in verdicts if not broken]
        scores[name] = {
            "traps_caught": share(sum(traps), len(traps)),
            "kept": share(sum(kept), len(kept)),
            "kappa": kappa(verdicts),
        }

    spent = round(sum(SPENT), 4)
    run = run_record(model=JUDGE_MODEL, scores=scores, per_judge=per_judge, cost=spent)
    save(RESULTS / f"assistant_judge_traps_{label}.json", {"run": run, "verdicts": found})
    print(json.dumps({"scores": scores, "cost": spent}, indent=1))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("page_context")
    parser.add_argument("guides")
    parser.add_argument("--label", default="run")
    parser.add_argument("--per-judge", type=int, default=8)
    args = parser.parse_args()
    asyncio.run(main(args.page_context, args.guides, args.label, args.per_judge))
