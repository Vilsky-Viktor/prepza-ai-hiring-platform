"""Made-up candidates for the integrity-signals eval (integrity_signals.py): honest ones by
ability with realistic answer times, and ones relaying questions to an AI, fully or in part.
No real candidate's answers are used (rule 20); every assumption is a named constant below.

Honest answers follow the Rasch model, P(right) = sigmoid(ability - difficulty). Honest times
follow van der Linden's lognormal model: log time = log(reading + thinking) - log speed + noise,
thinking longer the harder the question is for the candidate (8 s easy to about 40 s hard, as
the plan's research found). Relayed answers are the AI's own picks (datasets/ai_picks.json),
taking a roughly flat 20-40 s whatever the question (photograph, wait, find the option)."""

import math
import random

# Item difficulty by the test's level, on the ability scale (abilities ~ N(0, 1)); questions the
# AI gets wrong are harder for people too, by AI_WRONG_SHIFT.
LEVEL_MEAN = {"basic": -0.8, "medium": 0.0, "hard": 0.8}
AI_WRONG_SHIFT = 0.6
# Honest timing: thinking seconds at an even match, how much they grow with difficulty against
# ability (per unit), the spread of candidates' speed and of each answer's time (log scale).
THINK_SECONDS = 14
SPEED_SPREAD = 0.3
# Relaying: each candidate's own flat time, its spread per answer, and the reading of options
# that still follows length (finding the AI's answer among them).
RELAY_SECONDS = (20, 40)
RELAY_SPREAD = 0.25
RELAY_READING = 0.15

# Honest populations: typical, and the hardest for the signals (noisy times that barely follow
# difficulty, skimming).
HONEST = {
    "typical": {"ability": (0, 1), "noise": 0.45, "growth": 0.5, "skim": 0.15},
    "noisy": {"ability": (0, 1), "noise": 0.7, "growth": 0.2, "skim": 0.3},
    "weak": {"ability": (-1.5, 0.5), "noise": 0.5, "growth": 0.5, "skim": 0.15},
    "strong": {"ability": (1.5, 0.5), "noise": 0.5, "growth": 0.5, "skim": 0.15},
}
# Relaying candidates: every question, half of them at random, or the ones hard for them; with
# the AI setting they use (a relay of datasets/ai_picks.json).
CHEATING = {
    "relay_all_luna": {"relay": "all", "ai": "gpt-6-luna/none"},
    "relay_all_sol": {"relay": "all", "ai": "gpt-6.1-sol/low"},
    "relay_all_luna_medium": {"relay": "all", "ai": "gpt-6-luna/medium"},
    "relay_half": {"relay": "half", "ai": "gpt-6-luna/none"},
    "relay_hard": {"relay": "hard", "ai": "gpt-6-luna/none"},
}


def sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-value))


def honest_answer(item: dict, ability: float, rng: random.Random) -> list[int]:
    """The options picked: the right ones, or one wrong option."""
    if rng.random() < sigmoid(ability - item["b"]):
        return item["right"]

    wrong = [i for i in range(item["options"]) if i not in item["right"]]

    return [rng.choice(wrong)]


def honest_seconds(item: dict, person: dict, rng: random.Random, kind: dict) -> float:
    thinking = THINK_SECONDS * math.exp(kind["growth"] * (item["b"] - person["ability"]))
    reading = item["reading"] * (0.4 if rng.random() < kind["skim"] else 1.0)

    return (reading + thinking) / person["speed"] * math.exp(rng.gauss(0, kind["noise"]))


def relay_seconds(item: dict, person: dict, rng: random.Random) -> float:
    flat = person["relay"] * math.exp(rng.gauss(0, RELAY_SPREAD))

    return flat + RELAY_READING * item["reading"]


def person(rng: random.Random, kind: dict) -> dict:
    mean, spread = kind["ability"]

    return {
        "ability": rng.gauss(mean, spread),
        "speed": math.exp(rng.gauss(0, SPEED_SPREAD)),
        "relay": rng.uniform(*RELAY_SECONDS),
    }


def relayed(item: dict, who: dict, rng: random.Random, mode: str) -> bool:
    if mode == "all":
        return True

    if mode == "half":
        return rng.random() < 0.5

    return item["b"] > who["ability"]


def session(items: list[dict], rng: random.Random, honest: str | None, cheat: str | None):
    """One candidate's answers: rows as the signals read them."""
    kind = HONEST[honest or "typical"]
    cheating = CHEATING.get(cheat)
    who = person(rng, {**kind, "ability": (-0.5, 1)} if cheating else kind)
    rows = []

    for item in items:
        if cheating and relayed(item, who, rng, cheating["relay"]):
            picks = item["ai"][cheating["ai"]]
            seconds = relay_seconds(item, who, rng)
        else:
            picks = honest_answer(item, who["ability"], rng)
            seconds = honest_seconds(item, who, rng, kind)

        in_time = seconds <= item["limit"]
        rows.append(
            {
                "seconds": round(seconds) if in_time else None,
                "limit": item["limit"],
                "difficulty": item["p_seen"],
                "correct": in_time and picks == item["right"],
                "picks": picks if in_time else None,
            }
        )

    return rows
