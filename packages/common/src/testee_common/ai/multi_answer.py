"""Multi-answer ("select all that apply") questions: options shaped as every other question's
(`[{"answer", "correct"}]`), with 2 or 3 of the 4 correct, never all. Generation writes a share of
every topic this way (multi_share), and every candidate's draw from a topic holds the same share."""

import math
import random

from testee_common.limits.limits import limit


async def multi_share(redis) -> float:
    """The share of a topic's questions, and of each draw from it, that are multi-answer, 0 to 1:
    MULTI_ANSWER_PERCENT as set in the Controls tab, the same for every service that reads it
    (generation, library, rounds, companies)."""
    return await limit(redis, "MULTI_ANSWER_PERCENT") / 100


def correct_count(options: list) -> int:
    """How many options are marked correct; options as dicts or as models with `correct`."""
    return sum(
        1
        for option in options
        if (option["correct"] if isinstance(option, dict) else option.correct)
    )


def is_multi(options: list) -> bool:
    return correct_count(options) > 1


def multi_count(count: int, share: float) -> int:
    """How many of `count` questions are multi-answer: `share` of them (multi_share), rounded
    half up."""
    return math.floor(count * share + 0.5)


def draw(questions: list, count: int, share: float) -> list:
    """A fresh random `count` of a topic's questions ({"options", ...}), of which
    multi_count(count, share) are multi-answer and the rest single-answer. A topic short of one kind
    makes up with the other, so the draw keeps its size. The order is random."""
    if count >= len(questions):
        return random.sample(questions, len(questions))

    multi = [question for question in questions if is_multi(question["options"])]
    single = [question for question in questions if not is_multi(question["options"])]
    wanted = min(multi_count(count, share), len(multi))
    wanted = max(wanted, count - len(single))
    picked = random.sample(multi, wanted) + random.sample(single, count - wanted)
    random.shuffle(picked)

    return picked
