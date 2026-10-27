from types import SimpleNamespace

import pytest
from prepza_common.ai.examples import (
    example_count,
    example_language,
    example_range,
    has_example,
    is_formal,
    pick,
    pool_share,
)

SINGLE = [{"answer": "a", "correct": True}, {"answer": "b", "correct": False}]
MULTI = [{"answer": "a", "correct": True}, {"answer": "b", "correct": True}]
CODE = "What does it print?\n```python\nprint(1)\n```"
TABLE = "Which row is odd?\n```text\nid | name\n```"


def question(text="Why?", multi=False):
    return {"text": text, "options": MULTI if multi else SINGLE}


def test_an_example_is_a_fenced_block_and_its_language_is_the_fences():
    assert has_example(CODE) and not has_example("Why?")
    assert example_language(CODE) == "python"
    assert example_language(TABLE) == "text"
    assert example_language("Q?\n```\nx\n```") is None
    assert example_language("Why?") is None


@pytest.mark.parametrize(
    "count, formal, expected",
    [
        (90, True, (27, 36)),
        (30, True, (9, 12)),
        (60, True, (18, 24)),
        (70, True, (21, 28)),
        (90, False, (0, 36)),
        (2, True, (1, 1)),
        (1, True, (0, 0)),
    ],
)
def test_a_topic_holds_30_to_40_percent_with_an_example_on_formal_material(count, formal, expected):
    assert example_range(count, formal) == expected


def test_about_a_third_is_asked_for():
    assert [example_count(count) for count in (90, 30, 8, 1)] == [30, 10, 3, 0]


def test_a_topic_is_about_formal_material_when_enough_examples_are_in_a_colored_notation():
    plain = ["Why?"] * 17

    assert is_formal([CODE] * 3 + plain)
    assert not is_formal([CODE] * 2 + plain)
    # A table's rows ("text") don't make a topic formal, however many there are.
    assert not is_formal([TABLE] * 10 + plain)
    assert not is_formal([])


def test_picking_holds_each_kind_within_its_room():
    questions = [question(CODE)] * 6 + [question()] * 6 + [question(multi=True)] * 3
    taken, rest = pick(questions, 10, 2, (3, 4))

    assert len(taken) == 10 and len(rest) == 5
    assert sum(has_example(q["text"]) for q in taken) == 4
    assert sum(q["options"] is MULTI for q in taken) == 2


def test_each_pool_gets_its_share_of_multi_answer_questions_and_examples():
    fresh = (
        [question(CODE) for _ in range(30)]
        + [question() for _ in range(51)]
        + [question(multi=True) for _ in range(9)]
    )
    practice, company = pool_share(fresh, fresh, 30, 0.1)

    assert len(practice) == 30 and len(company) == 60
    assert sum(has_example(q["text"]) for q in practice) == 10
    assert sum(q["options"] is MULTI for q in practice) == 3


def test_a_pool_is_made_up_with_another_kind_when_one_runs_short():
    fresh = [SimpleNamespace(text=CODE, options=SINGLE) for _ in range(35)]
    practice, company = pool_share(fresh, fresh, 30, 0.1)

    assert len(practice) == 30 and len(company) == 5
