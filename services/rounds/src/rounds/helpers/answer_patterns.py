"""The statistics behind the answer-pattern signals, on one candidate's answers as rows of
{"seconds", "expected", "difficulty", "correct"}: `seconds` None when the time ran out,
`difficulty` the share of candidates who get the question right (None until known). The eval
(evals/scripts/integrity_signals.py) runs these same functions."""

import math
import statistics

from rounds.constants.answer_patterns import (
    ABILITY_RANGE,
    ABILITY_STEPS,
    DIFFICULTY_EDGE,
    MAX_PERSON_FIT,
    MAX_TIME_RHO,
    MAX_TIME_SPREAD,
    MIN_KNOWN_DIFFICULTY,
    MIN_TIMED_ANSWERS,
    RASCH_SCALE,
)


def ranks(values: list[float]) -> list[float]:
    """Each value's rank from 0, ties sharing their average rank."""
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


def spearman(first: list[float], second: list[float]) -> float | None:
    """Spearman's rho; None when either side doesn't vary."""
    a, b = ranks(first), ranks(second)
    mean_a, mean_b = statistics.mean(a), statistics.mean(b)
    top = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b, strict=True))
    bottom = (sum((x - mean_a) ** 2 for x in a) * sum((y - mean_b) ** 2 for y in b)) ** 0.5

    return top / bottom if bottom else None


def timing(rows: list[dict]) -> tuple[float, float] | None:
    """How much the answer times vary (the standard deviation of their logarithms) and how well
    they follow what each question predicts (Spearman's rho); None with too few answers in time,
    or nothing to compare (every question predicting the same)."""
    timed = [row for row in rows if row["seconds"] is not None]

    if len(timed) < MIN_TIMED_ANSWERS:
        return None

    rho = spearman([row["seconds"] for row in timed], [row["expected"] for row in timed])

    if rho is None:
        return None

    spread = statistics.stdev(math.log(max(1, row["seconds"])) for row in timed)

    return spread, rho


def flat_timing(rows: list[dict]) -> bool:
    """Times nearly the same on every question, not following what each one predicts: what
    relaying questions to an AI looks like."""
    found = timing(rows)

    return found is not None and found[0] <= MAX_TIME_SPREAD and found[1] <= MAX_TIME_RHO


def sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-value))


def rasch_difficulty(share_right: float) -> float:
    p = min(1 - DIFFICULTY_EDGE, max(DIFFICULTY_EDGE, share_right))

    return -math.log(p / (1 - p)) * RASCH_SCALE


def ability(score: int, difficulties: list[float]) -> float | None:
    """The ability whose expected score is `score` (maximum likelihood); None for none or all
    right, where it's unbounded."""
    if score in (0, len(difficulties)):
        return None

    low, high = -ABILITY_RANGE, ABILITY_RANGE

    for _ in range(ABILITY_STEPS):
        middle = (low + high) / 2

        if sum(sigmoid(middle - b) for b in difficulties) < score:
            low = middle
        else:
            high = middle

    return (low + high) / 2


def person_fit(rows: list[dict]) -> float | None:
    """The lz person-fit index (Drasgow, Levine and Williams 1985) over answers to questions of
    known difficulty: well below 0 when right and wrong answers don't follow difficulty. None
    with too few such answers, or every one right or every one wrong."""
    known = [row for row in rows if row["difficulty"] is not None]

    if len(known) < MIN_KNOWN_DIFFICULTY:
        return None

    difficulties = [rasch_difficulty(row["difficulty"]) for row in known]
    theta = ability(sum(row["correct"] for row in known), difficulties)

    if theta is None:
        return None

    observed = expected = variance = 0.0

    for row, b in zip(known, difficulties, strict=True):
        p = sigmoid(theta - b)
        observed += math.log(p) if row["correct"] else math.log(1 - p)
        expected += p * math.log(p) + (1 - p) * math.log(1 - p)
        variance += p * (1 - p) * math.log(p / (1 - p)) ** 2

    return (observed - expected) / math.sqrt(variance) if variance else None


def unusual_pattern(rows: list[dict]) -> bool:
    found = person_fit(rows)

    return found is not None and found <= MAX_PERSON_FIT


def by_difficulty(rows: list[dict]) -> list[dict]:
    """The answers to questions of known difficulty, the hardest (fewest right) first."""
    known = [row for row in rows if row["difficulty"] is not None]

    return sorted(known, key=lambda row: row["difficulty"])


def hard_half(rows: list[dict]) -> list[dict]:
    """The answers to the harder half of the questions of known difficulty."""
    known = by_difficulty(rows)

    return known[: len(known) // 2]


def pattern_counts(rows: list[dict]) -> dict[str, int]:
    """For the report's sentence: the harder half of the questions of known difficulty, how many
    of them right; the easier half, how many wrong."""
    known = by_difficulty(rows)
    hard, easy = known[: len(known) // 2], known[len(known) // 2 :]

    return {
        "hard": len(hard),
        "hard_right": sum(row["correct"] for row in hard),
        "easy": len(easy),
        "easy_wrong": sum(not row["correct"] for row in easy),
    }
