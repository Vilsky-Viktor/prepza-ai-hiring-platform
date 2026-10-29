"""The eval gate's decision before a quality pattern ships (evals/scripts/gate_checks.py): its
mistake must be rarer beyond the noise, and nothing else worse beyond it."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals" / "scripts"))

from gate_checks import decision, measures

SINGLE = {"options": [{"answer": "a", "correct": True}, {"answer": "b", "correct": False}]}
MULTI = {"options": [{"answer": "a", "correct": True}, {"answer": "b", "correct": True}]}


def judged(count: int, *, mistakes: int, clarity: int = 5, key_wrong: int = 0) -> dict:
    """A set of `count` questions (a quarter multi-answer), `mistakes` of them showing the
    pattern's mistake; the first `key_wrong` with a wrong key."""
    items = [MULTI if index % 4 == 0 else SINGLE for index in range(count)]
    reviews = [
        {
            "key_correct": index >= key_wrong,
            "clarity": clarity - index % 2,
            "relevance": 4 + index % 2,
            "distractors": 3 + index % 2,
            "seconds": 40 + index % 7,
        }
        for index in range(count)
    ]

    return measures(items, reviews, [index < mistakes for index in range(count)])


def test_a_rule_ships_when_its_mistake_gets_rarer_beyond_the_noise_and_nothing_gets_worse():
    ships, reasons = decision(judged(200, mistakes=60), judged(200, mistakes=6))

    assert (ships, reasons) == (True, [])


def test_a_rule_whose_mistake_moves_within_the_noise_doesnt_ship():
    ships, reasons = decision(judged(200, mistakes=10), judged(200, mistakes=7))

    assert not ships
    assert reasons == ["its mistake isn't rarer beyond the noise"]


def test_a_rule_that_makes_another_dimension_worse_beyond_the_noise_doesnt_ship():
    worse_keys = decision(judged(200, mistakes=60), judged(200, mistakes=6, key_wrong=60))
    worse_clarity = decision(judged(200, mistakes=60), judged(200, mistakes=6, clarity=3))

    assert worse_keys == (
        False,
        ["keys_single is worse beyond the noise", "keys_multi is worse beyond the noise"],
    )
    assert worse_clarity == (False, ["clarity is worse beyond the noise"])


def test_each_dimension_has_its_interval_and_a_set_without_multi_answer_ones_has_none():
    found = measures(
        [SINGLE, SINGLE],
        [{"key_correct": True, "clarity": 5, "relevance": 4, "distractors": 3, "seconds": 30}] * 2,
        [False, True],
    )

    assert found["keys_multi"] is None
    assert found["keys_single"][0] == 1.0
    assert found["mistake"][0] == 0.5 and found["mistake"][1] < 0.5 < found["mistake"][2]
    assert found["clarity"] == (5, 5, 5)
