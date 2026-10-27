import asyncio

import pytest
from fake_redis import DownRedis, FakeRedis
from prepza_common.ai.multi_answer import correct_count, draw, is_multi, multi_count, multi_share

SINGLE = [{"answer": "a", "correct": True}, {"answer": "b", "correct": False}]
MULTI = [
    {"answer": "a", "correct": True},
    {"answer": "b", "correct": True},
    {"answer": "c", "correct": False},
    {"answer": "d", "correct": False},
]


class Option:
    def __init__(self, correct):
        self.correct = correct


def topic(single, multi):
    return [{"id": f"s{index}", "options": SINGLE} for index in range(single)] + [
        {"id": f"m{index}", "options": MULTI} for index in range(multi)
    ]


def kinds(questions):
    return sum(is_multi(question["options"]) for question in questions)


def test_a_question_with_more_than_one_right_option_is_multi_answer():
    assert (correct_count(SINGLE), correct_count(MULTI)) == (1, 2)
    assert (is_multi(SINGLE), is_multi(MULTI)) == (False, True)
    # Options as models too.
    assert is_multi([Option(True), Option(True), Option(False)])
    assert not is_multi([Option(True), Option(False)])


@pytest.mark.parametrize(
    ("count", "share", "multi"),
    [(10, 0.1, 1), (30, 0.1, 3), (4, 0.1, 0), (5, 0.1, 1), (14, 0.1, 1), (15, 0.1, 2), (10, 0, 0)],
)
def test_the_multi_answer_share_of_a_count_is_rounded_half_up(count, share, multi):
    assert multi_count(count, share) == multi


@pytest.mark.parametrize(
    ("redis", "share"),
    [
        (FakeRedis(), 0.1),
        (FakeRedis({"MULTI_ANSWER_PERCENT": "25.0"}), 0.25),
        (FakeRedis({"MULTI_ANSWER_PERCENT": "0"}), 0),
        (DownRedis(), 0.1),
    ],
)
def test_the_share_is_the_percent_set_in_controls_or_its_default(redis, share):
    assert asyncio.run(multi_share(redis)) == share


def test_a_draw_holds_the_share_of_multi_answer_questions():
    questions = topic(30, 10)

    for _ in range(20):
        drawn = draw(questions, 20, 0.1)

        assert len(drawn) == 20 and len({question["id"] for question in drawn}) == 20
        assert kinds(drawn) == 2


def test_a_topic_short_of_one_kind_makes_up_with_the_other():
    # No multi-answer questions: all single.
    assert kinds(draw(topic(30, 0), 20, 0.1)) == 0
    # One multi-answer question where the share is two.
    assert kinds(draw(topic(30, 1), 20, 0.1)) == 1
    # Only 5 single-answer questions: the other 15 are multi-answer.
    assert kinds(draw(topic(5, 30), 20, 0.1)) == 15


def test_a_draw_of_the_whole_topic_takes_every_question_in_a_random_order():
    questions = topic(6, 2)
    drawn = draw(questions, 10, 0.1)

    assert sorted(question["id"] for question in drawn) == sorted(q["id"] for q in questions)
    assert len(draw(questions, 8, 0.1)) == 8
