import uuid

import pytest
from testee_common.ai.multi_answer import is_multi
from testee_common.ai.sets import QuestionIn

from tests.unit.api.v1.test_additions import context, run_addition, topic
from tests.unit.fakes import EXAMPLE, MULTI_OPTIONS, OPTIONS


@pytest.fixture(autouse=True)
def a_fifth_multi_answer(redis):
    """As set in the Controls tab."""
    redis.limits["MULTI_ANSWER_PERCENT"] = "20"


def multi(questions):
    return sum(is_multi(question.options) for question in questions)


def test_each_side_of_an_addition_gets_its_share_of_multi_answer_questions(monkeypatch, writer):
    run_addition(monkeypatch, context(topic()), 30)

    [saved] = writer["saved"]
    [added] = saved.topics

    assert (len(added.practice), multi(added.practice)) == (10, 2)
    assert (len(added.company), multi(added.company)) == (20, 4)
    # The calls are asked for the six between them.
    assert sum(task["multi"] for task in writer["tasks"]) == 6


def test_multi_answer_bank_questions_count_toward_the_company_side(monkeypatch, writer):
    writer["bank"] = [
        QuestionIn(
            text=f"Bank {index}?",
            options=MULTI_OPTIONS if index < 3 else OPTIONS,
            source_id=uuid.uuid4(),
        )
        for index in range(10)
    ]

    run_addition(monkeypatch, context(topic()), 30)

    [saved] = writer["saved"]
    [added] = saved.topics
    fresh = [question for question in added.company if question.source_id is None]

    assert (len(added.company), multi(added.company)) == (20, 4)
    assert (len(fresh), multi(fresh)) == (10, 1)
    assert multi(added.practice) == 2


def test_multi_answer_questions_that_never_come_are_made_up_with_single_ones(monkeypatch, writer):
    writer["no_multi"] = True

    run_addition(monkeypatch, context(topic()), 30)

    [saved] = writer["saved"]
    [added] = saved.topics

    assert [len(added.practice), len(added.company)] == [10, 20]
    assert multi(added.practice) + multi(added.company) == 0


def shown(questions):
    return sum("```" in question.text for question in questions)


# A topic on formal material: a third of its questions show code.
FORMAL_TEXTS = [f"Old {index}?" + (EXAMPLE if index % 3 == 0 else "") for index in range(90)]


def test_each_side_of_an_addition_gets_its_share_of_questions_with_an_example(monkeypatch, writer):
    run_addition(monkeypatch, context(topic(texts=FORMAL_TEXTS)), 30)

    [saved] = writer["saved"]
    [added] = saved.topics

    # 30% to 40% of each side: 3 or 4 of the 10 practice, 6 to 8 of the 20 company questions.
    assert 3 <= shown(added.practice) <= 4
    assert 6 <= shown(added.company) <= 8
    assert sum(task["examples"] for task in writer["tasks"]) == 10


def test_examples_that_dont_come_are_topped_up_as_their_own_kind(monkeypatch, writer):
    writer["no_examples"] = True

    run_addition(monkeypatch, context(topic(texts=FORMAL_TEXTS)), 30)

    [saved] = writer["saved"]
    [added] = saved.topics

    assert [len(added.practice), len(added.company)] == [10, 20]
    assert shown(added.practice + added.company) == 9
    assert {(multi, example) for multi, example, _ in writer["fills"]} == {(False, True)}


def test_a_topic_on_other_material_is_held_only_to_the_upper_bound(monkeypatch, writer):
    run_addition(monkeypatch, context(topic(texts=["Old?"] * 90)), 30)

    [saved] = writer["saved"]
    [added] = saved.topics

    assert shown(added.practice) <= 4 and shown(added.company) <= 8
    assert writer["fills"] == []
