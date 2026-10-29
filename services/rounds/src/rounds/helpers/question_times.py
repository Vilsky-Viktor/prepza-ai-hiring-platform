"""Each question's own time: its weight from how long it takes to read and answer, scaled so a
candidate's questions add up to exactly questions × the average (the interview's setting, with
their extra time), each kept between MIN_SHARE and MAX_SHARE of the average."""

import math
import re

from rounds.constants.question_times import (
    ANSWER_SECONDS,
    EXAMPLE_WORDS_PER_MINUTE,
    MAX_SHARE,
    MIN_SHARE,
    TEXT_WORDS_PER_MINUTE,
    TYPICAL_SECONDS,
    WEIGHT_ONE_SCRIPTS,
)

FENCE = re.compile(r"```[\w+-]*\n(.*?)\n?```", re.DOTALL)
WEIGHT_ONE = re.compile(WEIGHT_ONE_SCRIPTS)
# Bisection steps for the scale: far past a second's precision for any interview.
SCALE_STEPS = 60


def estimated_seconds(question: dict) -> float:
    """How long the question takes: reading its text and options, its example (code, a query, a
    table's rows) more slowly, plus the time to answer."""
    text = question["text"]
    options = " ".join(option["answer"] for option in question["options"])
    example = " ".join(FENCE.findall(text))
    words = len((FENCE.sub(" ", text) + " " + options).split())

    return (
        60 * words / TEXT_WORDS_PER_MINUTE
        + 60 * len(example.split()) / EXAMPLE_WORDS_PER_MINUTE
        + ANSWER_SECONDS
    )


def question_weight(question: dict) -> float:
    """How long the question takes against a typical one; 1 in a script whose estimate doesn't
    follow the judge's (constants/question_times.py WEIGHT_ONE_SCRIPTS)."""
    options = " ".join(option["answer"] for option in question["options"])

    if WEIGHT_ONE.search(question["text"] + options):
        return 1.0

    return estimated_seconds(question) / TYPICAL_SECONDS


def limits(average: int) -> tuple[int, int]:
    """The shortest and longest time a question may get, in whole seconds."""
    return math.ceil(MIN_SHARE * average), MAX_SHARE * average


def scaled(weights: list[float], scale: float, average: int) -> list[float]:
    """Each weight times `scale`, kept within the limits."""
    low, high = limits(average)

    return [min(high, max(low, weight * scale)) for weight in weights]


def fitted(weights: list[float], average: int) -> list[float]:
    """Times in proportion to `weights`, each between the limits, adding up to exactly
    len(weights) × average: a time a limit cuts is spread over the others, in proportion. The
    scale is found by bisection, as the sum of the cut times grows with it."""
    total = len(weights) * average
    small, large = 0.0, limits(average)[1] / min(weights)

    for _ in range(SCALE_STEPS):
        middle = (small + large) / 2

        if sum(scaled(weights, middle, average)) < total:
            small = middle
        else:
            large = middle

    return scaled(weights, large, average)


def fitted_seconds(weights: list[float], average: int) -> list[int]:
    """Whole seconds a question, adding up to exactly len(weights) × average: each time rounded
    down, and the seconds left one each to the longest questions still under the limit."""
    times = fitted(weights, average)
    seconds = [math.floor(time) for time in times]
    left = len(weights) * average - sum(seconds)
    longest = sorted(range(len(times)), key=lambda index: -times[index])

    for index in longest:
        if left <= 0:
            break

        if seconds[index] < limits(average)[1]:
            seconds[index] += 1
            left -= 1

    return seconds


def add_times(questions: list[dict], average: int | None) -> None:
    """Gives each of a candidate's questions its own `seconds`; none when untimed."""
    if average is None or not questions:
        return

    weights = [question_weight(question) for question in questions]

    for question, seconds in zip(questions, fitted_seconds(weights, average), strict=True):
        question["seconds"] = seconds
