"""Answer-pattern integrity signals (internal_docs/plans/anti-cheating.md): how many honest
candidates each signal flags, and how many relaying ones it catches, across its thresholds, on
made-up candidates (integrity_population.py) answering the eval's real questions with their
fitted times and the AI's real picks (datasets/ai_picks.json). Code only, free:

    evals/run.sh rounds integrity_signals.py [--sessions 3000]

The statistics are rounds' own (helpers/answer_patterns.py), and "any signal" uses rounds'
thresholds. A threshold is chosen as the loosest one that flags at most TARGET of every honest
population, the noisiest included. AI-trap questions were measured by ai_picks.py and dropped."""

import argparse
import random
import time
from collections import defaultdict

from ai_picks import PICKS, SETS, right_set
from common import DATASETS, RESULTS, load, question_items, run_record, save
from integrity_population import AI_WRONG_SHIFT, CHEATING, HONEST, LEVEL_MEAN, session, sigmoid
from stats import share

from rounds.constants.answer_patterns import (
    MAX_PERSON_FIT,
    MAX_TIME_RHO,
    MAX_TIME_SPREAD,
    RASCH_SCALE,
)
from rounds.constants.question_times import ANSWER_SECONDS
from rounds.helpers.answer_patterns import person_fit, timing
from rounds.helpers.integrity_report import expected_seconds
from rounds.helpers.question_times import estimated_seconds, fitted_seconds, question_weight

TARGET = 0.01
AVERAGE = {"basic": 60, "medium": 60, "hard": 75}
# Answers a question has before its difficulty is known (the rest have none).
ANSWERS_KNOWN = 30
THRESHOLDS = {
    "timing_flat": [(s, r) for s in (0.25, 0.3, 0.35, 0.4) for r in (0.0, 0.2, 0.4, 1.0)],
    "person_fit": [-2.0, -2.5, -3.0, -3.5, -4.0, -4.5],
}
# rounds' thresholds, chosen on the full runs (30, 20 and 10 questions): each flags at most TARGET
# of every honest population at every size.
CHOSEN = {"timing_flat": (MAX_TIME_SPREAD, MAX_TIME_RHO), "person_fit": MAX_PERSON_FIT}


def items(rng: random.Random) -> dict[tuple, list[dict]]:
    """Every question as the simulation sees it, grouped into the interviews they can form."""
    picks = {(e["set"], e["id"]): e for e in load(DATASETS / "ai_picks.json")["items"]}
    groups = defaultdict(list)

    for name in SETS:
        for item in question_items(DATASETS / name):
            entry = picks[(name, item["id"])]
            right = right_set(item)
            question = {"text": item["question"], "options": item["options"]}
            ai = {k: v if v is not None else [-1] for k, v in entry["relays"].items()}
            b = rng.gauss(LEVEL_MEAN[item["level"]], 1)
            b += AI_WRONG_SHIFT if ai[PICKS[1]] != right else 0
            p = sigmoid(-b / RASCH_SCALE)
            seen = sum(rng.random() < p for _ in range(ANSWERS_KNOWN)) / ANSWERS_KNOWN
            groups[(name, item["domain"], item["level"])].append(
                {
                    "right": right,
                    "options": len(item["options"]),
                    "ai": ai,
                    "b": b,
                    "p_seen": max(seen, 1 / ANSWERS_KNOWN),
                    "reading": estimated_seconds(question) - ANSWER_SECONDS,
                    "weight": question_weight(question),
                }
            )

    return groups


def interview(group: list[dict], level: str, count: int, rng: random.Random):
    chosen = rng.sample(group, min(count, len(group)))
    seconds = fitted_seconds([item["weight"] for item in chosen], AVERAGE[level])

    return [{**item, "limit": limit} for item, limit in zip(chosen, seconds, strict=True)]


def statistics_of(rows: list[dict]) -> dict:
    shaped = [
        {**row, "expected": expected_seconds(row["limit"], row["difficulty"])} for row in rows
    ]
    return {"timing_flat": timing(shaped), "person_fit": person_fit(rows)}


def fires(signal: str, value, threshold) -> bool:
    if value is None:
        return False

    if signal == "timing_flat":
        return value[0] <= threshold[0] and value[1] <= threshold[1]

    return value <= threshold


def simulate(args, groups, rng) -> dict[str, list[dict]]:
    populations = [(name, None) for name in HONEST] + [("typical", name) for name in CHEATING]
    found = {}
    keys = list(groups)

    for honest, cheat in populations:
        label = cheat or f"honest_{honest}"
        found[label] = []

        for _ in range(args.sessions):
            key = rng.choice(keys)
            asked = interview(groups[key], key[2], args.questions, rng)
            found[label].append(statistics_of(session(asked, rng, honest, cheat)))

    return found


def report(found: dict[str, list[dict]]) -> dict:
    scores = {}

    for signal, grid in THRESHOLDS.items():
        rows = []

        for threshold in grid:
            rates = {
                label: sum(fires(signal, s[signal], threshold) for s in stats) / len(stats)
                for label, stats in found.items()
            }
            honest = max(rate for label, rate in rates.items() if label.startswith("honest"))
            rows.append({"threshold": threshold, "honest_max": round(honest, 4), **rates})

        passing = [row for row in rows if row["honest_max"] <= TARGET]
        chosen = max(passing, key=lambda row: row["relay_all_luna"], default=None)
        scores[signal] = {"grid": rows, "chosen": chosen}
        print(signal)

        for row in rows:
            print("  ", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()})

    return scores


def combined(found: dict, chosen: dict) -> dict:
    """Any signal at its chosen threshold, per population, with the interval."""
    result = {}

    for label, stats in found.items():
        hits = sum(
            any(
                fires(signal, s[signal], pick["threshold"])
                for signal, pick in chosen.items()
                if pick
            )
            for s in stats
        )
        result[label] = share(hits, len(stats))

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessions", type=int, default=3000)
    parser.add_argument("--questions", type=int, default=30)
    parser.add_argument("--seed", type=int, default=11)
    args = parser.parse_args()
    started = time.monotonic()
    rng = random.Random(args.seed)
    groups = items(rng)
    found = simulate(args, groups, rng)
    scores = report(found)
    chosen = {signal: {"threshold": threshold} for signal, threshold in CHOSEN.items()}
    together = combined(found, chosen)
    print("any signal:", together)
    run = run_record(
        dataset="ai_picks.json + simulated candidates",
        sessions=args.sessions,
        questions=args.questions,
        scores={"signals": scores, "any": together},
        cost=0,
        seconds=round(time.monotonic() - started),
    )
    save(RESULTS / f"integrity_signals_q{args.questions}.json", {"run": run})


if __name__ == "__main__":
    main()
