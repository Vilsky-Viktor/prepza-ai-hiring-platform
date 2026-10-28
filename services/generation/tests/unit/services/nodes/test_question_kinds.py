import asyncio

import pytest
from prepza_common.ai.examples import pick

from generation.helpers.questions import build_options, count_examples, count_multi, missing_kinds
from generation.services.nodes import merge as merge_node
from generation.services.nodes.fan_out import fan_out_questions
from generation.services.nodes.merge import merge_questions
from tests.unit.fakes import EXAMPLE, MULTI_OPTIONS, OPTIONS


def right(options):
    return sorted(option["answer"] for option in options if option["correct"])


def question(text, multi=False):
    return {"text": text, "options": MULTI_OPTIONS if multi else OPTIONS}


def test_a_multi_answer_question_has_two_or_three_right_of_four_options():
    two = build_options(["R1", "R2"], ["W1", "W2", "W3"])
    three = build_options(["R1", "R2", "R3"], ["W1"])

    assert len(two) == 4 and right(two) == ["R1", "R2"]
    assert len(three) == 4 and right(three) == ["R1", "R2", "R3"]
    # Every option right, a repeated right one, or too few options don't qualify.
    assert build_options(["R1", "R2", "R3", "R4"], []) is None
    assert build_options(["R1", "r1"], ["W1", "W2", "W3"]) is None
    assert build_options(["R1", "R2"], ["W1"]) is None


def test_options_of_the_other_kind_are_refused_when_a_kind_is_asked_for():
    assert build_options(["R1"], ["W1", "W2", "W3"], multi=True) is None
    assert build_options(["R1", "R2"], ["W1", "W2"], multi=False) is None
    assert right(build_options(["R1", "R2"], ["W1", "W2"], multi=True)) == ["R1", "R2"]
    assert right(build_options(["R1"], ["W1", "W2", "W3"], multi=False)) == ["R1"]


def test_a_topic_lacks_each_kind_up_to_its_share():
    def lacking(have, have_multi, multi=2, examples=(0, 4), have_examples=0):
        questions = [
            question(f"Q{i}" + (EXAMPLE if i >= have - have_examples else ""), i < have_multi)
            for i in range(have)
        ]
        kinds = missing_kinds(10, questions, multi, examples)

        # (single, multi) as before, and the questions with an example among them.
        return (
            kinds[False, False] + kinds[False, True],
            kinds[True, False] + kinds[True, True],
            kinds[False, True] + kinds[True, True],
        )

    assert lacking(0, 0) == (8, 2, 0)
    assert lacking(7, 0) == (1, 2, 0)
    assert lacking(9, 0) == (0, 1, 0)
    # Multi-answer ones it has count toward the share; a full topic lacks nothing.
    assert lacking(5, 1) == (4, 1, 0)
    assert lacking(5, 3) == (5, 0, 0)
    assert lacking(10, 0) == (0, 0, 0)
    assert lacking(12, 0) == (0, 0, 0)
    # On material in a formal notation, the fewest with an example too; ones it has count.
    assert lacking(0, 0, examples=(3, 4)) == (8, 2, 3)
    assert lacking(5, 0, examples=(3, 4), have_examples=2) == (3, 2, 1)
    assert lacking(9, 0, examples=(3, 4)) == (0, 1, 1)


def test_questions_are_counted_and_taken_by_kind():
    questions = [question("S1"), question("M1", True), question("S2"), question("M2", True)]
    taken, rest = pick(questions + [question("S3")], 3, 1, (0, 3))

    assert count_multi(questions) == 2
    assert [item["text"] for item in taken] == ["S1", "M1", "S2"]
    assert [item["text"] for item in rest] == ["M2", "S3"]


def test_questions_with_an_example_are_taken_within_their_range():
    plain = [question(f"P{i}") for i in range(6)]
    shown = [question(f"E{i}{EXAMPLE}") for i in range(6)]

    # At most 4 of 10 with one, and at least 3: the plain ones leave room for them.
    taken = pick(shown + plain, 10, 0, (3, 4))[0]

    assert count_examples(taken) == 4 and len(taken) == 10
    assert count_examples(pick(plain + shown, 10, 0, (3, 4))[0]) == 4
    assert len(pick(plain + shown[:2], 10, 0, (3, 4))[0]) == 2 + 7 - 1


def topics_state(reused=None, **extra):
    """Ten questions a topic, two of them multi-answer, unless `extra` says otherwise."""
    return {
        "topic_size": 10,
        "topics": [{"main_topic": "Bookkeeping", "subtopics": ["Cash", "Payroll"]}],
        "reused": [reused or []],
        "level": "basic",
        "language": "en",
        "multi_share": 0.2,
        **extra,
    }


def test_the_multi_answer_questions_a_topic_lacks_are_spread_over_its_calls(monkeypatch):
    tasks = [send.arg for send in fan_out_questions(topics_state(topic_size=70))]
    multis = [task["multi"] for task in tasks]

    assert len(tasks) > 1
    assert sum(multis) == 14
    assert max(multis) - min(multis) <= 1
    assert all(task["multi"] <= task["count"] for task in tasks)

    # Reused multi-answer questions count toward the topic's share.
    reused = [question("Proven 1", True), question("Proven 2", True), question("Proven 3")]
    tasks = [send.arg for send in fan_out_questions(topics_state(reused, topic_size=70))]

    assert sum(task["multi"] for task in tasks) == 12


def test_merging_takes_each_kind_up_to_what_the_topic_lacks(monkeypatch):
    async def all_distinct(texts, keep_first=0):
        return list(range(len(texts)))

    monkeypatch.setattr(merge_node, "distinct_by_meaning", all_distinct)
    singles = [question(f"S{i}") for i in range(12)]
    multis = [question(f"M{i}", True) for i in range(5)]
    pool = [
        {"topic_index": 0, "subtopic_index": 0, "questions": singles[:6] + multis},
        {"topic_index": 0, "subtopic_index": 1, "questions": singles[6:]},
    ]

    [merged] = asyncio.run(merge_questions(topics_state(question_pool=pool)))["topic_questions"]

    assert len(merged) == 10
    assert count_multi(merged) == 2

    # A reused multi-answer question leaves room for one more.
    reused = [question("Proven", True)]
    state = topics_state(reused, question_pool=pool)
    [merged] = asyncio.run(merge_questions(state))["topic_questions"]

    assert len(merged) == 9
    assert count_multi(merged) == 1


def test_a_third_with_an_example_is_asked_for_over_a_topics_calls(monkeypatch):
    tasks = [send.arg for send in fan_out_questions(topics_state(topic_size=70))]
    examples = [task["examples"] for task in tasks]

    assert sum(examples) == 23
    assert max(examples) - min(examples) <= 1
    assert all(task["examples"] <= task["count"] for task in tasks)


@pytest.mark.parametrize("language, low", [("python", 3), ("text", 0)])
def test_merging_holds_a_topics_examples_to_its_range(monkeypatch, language, low):
    """A topic whose examples are in a colored notation gets 30-40% with one; any other topic
    at most 40%."""

    async def all_distinct(texts, keep_first=0):
        return list(range(len(texts)))

    monkeypatch.setattr(merge_node, "distinct_by_meaning", all_distinct)
    shown = [question(f"E{i}\n```{language}\nx\n```") for i in range(8)]
    plain = [question(f"P{i}") for i in range(12)]
    pool = [{"topic_index": 0, "subtopic_index": 0, "questions": shown + plain}]

    [merged] = asyncio.run(merge_questions(topics_state(question_pool=pool, multi_share=0)))[
        "topic_questions"
    ]

    assert len(merged) == 10
    assert count_examples(merged) == 4

    # Plain ones first: a formal topic still keeps room for its fewest examples.
    pool = [{"topic_index": 0, "subtopic_index": 0, "questions": plain + shown[:3]}]
    [merged] = asyncio.run(merge_questions(topics_state(question_pool=pool, multi_share=0)))[
        "topic_questions"
    ]

    assert len(merged) == 10
    assert count_examples(merged) == low
