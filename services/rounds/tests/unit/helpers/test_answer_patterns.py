import math

import pytest

from rounds.constants.answer_patterns import (
    MAX_PERSON_FIT,
    MAX_TIME_RHO,
    MAX_TIME_SPREAD,
    MIN_KNOWN_DIFFICULTY,
    MIN_TIMED_ANSWERS,
)
from rounds.helpers.answer_patterns import (
    ability,
    flat_timing,
    hard_half,
    pattern_counts,
    person_fit,
    spearman,
    timing,
    unusual_pattern,
)


def row(seconds=None, expected=60.0, difficulty=None, correct=True) -> dict:
    return {"seconds": seconds, "expected": expected, "difficulty": difficulty, "correct": correct}


def test_spearman_ranks_ties_together_and_is_none_when_a_side_doesnt_vary():
    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1)
    assert spearman([1, 2, 3, 4], [40, 30, 20, 10]) == pytest.approx(-1)
    assert spearman([1, 1, 2, 2], [1, 1, 2, 2]) == pytest.approx(1)
    assert spearman([1, 2, 3], [5, 5, 5]) is None


def test_honest_times_that_rise_with_each_questions_time_dont_fire():
    rows = [row(seconds=s, expected=e) for s, e in zip([12, 20, 33, 41, 55, 70, 88, 95], range(8))]

    assert not flat_timing(rows)
    assert timing(rows)[1] > MAX_TIME_RHO


def test_the_same_time_on_every_question_against_their_times_fires():
    # 24-30 s on questions predicting 30 s to 120 s, the longest the quickest.
    rows = [row(seconds=30 - i % 7, expected=30 + 12 * i) for i in range(10)]
    spread, rho = timing(rows)

    assert spread <= MAX_TIME_SPREAD
    assert rho <= MAX_TIME_RHO
    assert flat_timing(rows)


def test_flat_times_that_still_follow_the_questions_dont_fire():
    rows = [row(seconds=24 + i % 7, expected=30 + 12 * (i % 7)) for i in range(10)]

    assert timing(rows)[0] <= MAX_TIME_SPREAD
    assert not flat_timing(rows)


def test_timing_needs_enough_answers_in_time_and_questions_that_differ():
    too_few = [row(seconds=25, expected=30 + i) for i in range(MIN_TIMED_ANSWERS - 1)]
    timed_out = too_few + [row(seconds=None, expected=200)]
    same_time = [row(seconds=20 + i, expected=60) for i in range(10)]

    assert timing(too_few) is None
    assert timing(timed_out) is None
    assert timing(same_time) is None
    assert not flat_timing(same_time)


def test_the_ability_matches_the_score_and_is_unbounded_for_none_or_all_right():
    difficulties = [-1.0, 0.0, 1.0]

    assert ability(0, difficulties) is None
    assert ability(3, difficulties) is None
    assert ability(1, difficulties) < ability(2, difficulties)
    assert ability(2, [0.0, 0.0, 0.0, 0.0]) == pytest.approx(0, abs=1e-6)


def pattern(hard_right: int, easy_wrong: int, size: int = 10) -> list[dict]:
    """`size` hard questions (20% right) and `size` easy ones (90% right)."""
    hard = [row(difficulty=0.2, correct=i < hard_right) for i in range(size)]
    easy = [row(difficulty=0.9, correct=i >= easy_wrong) for i in range(size)]

    return hard + easy


def test_hard_right_and_easy_wrong_is_an_unusual_pattern():
    reversed_ = pattern(hard_right=10, easy_wrong=8)

    assert person_fit(reversed_) <= MAX_PERSON_FIT
    assert unusual_pattern(reversed_)


def test_easy_right_and_hard_wrong_is_the_usual_pattern():
    usual = pattern(hard_right=2, easy_wrong=1)

    # Within the ordinary spread of an index about normal around 0.
    assert -2 < person_fit(usual) < 2
    assert not unusual_pattern(usual)


def test_person_fit_needs_enough_known_difficulties_and_a_mixed_score():
    few = pattern(hard_right=3, easy_wrong=1, size=MIN_KNOWN_DIFFICULTY // 2 - 1)
    unknown = [row(difficulty=None, correct=i % 2 == 0) for i in range(20)]
    all_right = pattern(hard_right=10, easy_wrong=0)

    assert person_fit(few) is None
    assert person_fit(unknown) is None
    assert person_fit(all_right) is None


def test_lz_is_finite_at_the_ends_of_difficulty():
    rows = [row(difficulty=d, correct=i % 2 == 0) for i, d in enumerate([0.0, 1.0] * 5)]

    assert math.isfinite(person_fit(rows))


def test_the_sentence_counts_the_hard_half_right_and_the_easy_half_wrong():
    rows = pattern(hard_right=9, easy_wrong=4) + [row(difficulty=None, correct=False)]

    assert pattern_counts(rows) == {"hard": 10, "hard_right": 9, "easy": 10, "easy_wrong": 4}
    assert all(r["difficulty"] == 0.2 for r in hard_half(rows))
