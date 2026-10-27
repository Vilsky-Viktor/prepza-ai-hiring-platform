from types import SimpleNamespace
from uuid import uuid4

import pytest
from prepza_common.ai.multi_answer import multi_count
from pydantic import ValidationError

from app.constants.practice import PRACTICE_TOPIC_QUESTIONS
from app.helpers.export import answer_export
from app.helpers.practice import practice_topics
from app.helpers.review import build_review
from app.helpers.rounds import next_question
from app.helpers.scores import answer_score, scored
from app.schemas.rounds import AnswerCreate

# Two right options of four: A and C.
MULTI = [
    {"answer": "A", "correct": True},
    {"answer": "B", "correct": False},
    {"answer": "C", "correct": True},
    {"answer": "D", "correct": False},
]
SINGLE = [{"answer": "A", "correct": True}, {"answer": "B", "correct": False}]


@pytest.mark.parametrize(
    "answer",
    [
        {},
        {"option_index": 0, "picks": [0]},
        {"picks": []},
        {"picks": [1, 1]},
        {"picks": [0, 4]},
        {"picks": [-1]},
        {"picks": [0, 1, 2, 3, 0]},
    ],
)
def test_an_answer_is_one_pick_or_distinct_ticks(answer):
    with pytest.raises(ValidationError):
        AnswerCreate(question_id=uuid4(), **answer)


def test_an_answers_choice_reads_the_same_either_way():
    assert AnswerCreate(question_id=uuid4(), picks=[3, 0, 2]).picked() == [0, 2, 3]
    assert AnswerCreate(question_id=uuid4(), option_index=1).picked() == [1]


@pytest.mark.parametrize(
    ("right", "picked", "score"),
    [
        ([0], [0], 100),
        ([0], [1], 0),
        ([0, 2, 3], [0, 2, 3], 100),
        ([0, 2, 3], [0, 3], 67),
        ([0, 2, 3], [2], 33),
        ([0, 2], [0], 50),
        # Any wrong option ticked costs every point.
        ([0, 2, 3], [0, 2, 3, 1], 0),
        ([0, 2], [], 0),
    ],
)
def test_an_answer_scores_its_share_of_right_options_and_nothing_with_a_wrong_one(
    right, picked, score
):
    assert answer_score(right, picked) == score


def answer(**fields):
    base = {
        "id": uuid4(),
        "option_index": None,
        "picks": None,
        "timed_out": False,
        "correct": False,
        "score": 0,
        "seconds": 20,
        "created_at": None,
    }

    return SimpleNamespace(**(base | fields))


def round_of(*answered):
    """A round of a multi-answer and a single-answer question, with the answers given."""
    questions = [
        {"id": str(uuid4()), "text": "Which are assets?", "options": MULTI},
        {"id": str(uuid4()), "text": "Which is cash?", "options": SINGLE},
    ]
    answers = [
        item | {"question_id": questions[index]["id"]} for index, item in enumerate(answered)
    ]

    return SimpleNamespace(
        questions=questions,
        answers=[answer(**item) for item in answers],
        signals=[],
        final_score=None,
    )


def test_a_review_shows_each_questions_right_options_and_what_the_answer_ticked():
    ticked = {"picks": [0, 1], "score": 0}
    picked = {"option_index": 0, "correct": True, "score": 100}
    multi, single = build_review(round_of(ticked, picked))

    assert (multi.multi, multi.correct_option_index, multi.correct_indexes) == (True, None, [0, 2])
    assert (multi.answer.picks, multi.answer.right_picks, multi.answer.wrong_picks) == (
        [0, 1],
        1,
        1,
    )
    assert (multi.answer.score, multi.answer.timed_out) == (0, False)
    assert (single.multi, single.correct_option_index, single.correct_indexes) == (False, 0, [0])
    assert (single.answer.picks, single.answer.right_picks, single.answer.score) == ([0], 1, 100)


def test_a_review_shows_a_timed_out_answer_with_nothing_picked():
    item, _ = build_review(round_of({"timed_out": True, "seconds": 30}))

    assert (item.answer.timed_out, item.answer.picks, item.answer.fast) == (True, [], False)
    assert (item.answer.right_picks, item.answer.wrong_picks) == (0, 0)


def test_a_review_hides_the_right_options_of_an_unanswered_question_until_all_are_shown():
    row = round_of()

    assert [item.correct_indexes for item in build_review(row)] == [None, None]
    assert [item.correct_indexes for item in build_review(row, reveal_all=True)] == [[0, 2], [0]]


def test_a_finished_section_tells_library_the_credit_of_a_partly_right_answer():
    row = round_of({"picks": [0], "score": 50}, {"timed_out": True})
    row.final_score = 25

    assert [(item["credit"], item["timed_out"]) for item in scored(row)["answers"]] == [
        (0.5, False),
        (0.0, True),
    ]


def test_the_data_export_lists_every_option_ticked():
    row = round_of({"picks": [0, 2], "correct": True, "score": 100}, {"timed_out": True})
    ticked, ran_out = (answer_export(row.questions, item, practice=True) for item in row.answers)

    assert (ticked["your_answer"], ticked["correct"]) == ("A; C", True)
    assert ran_out["your_answer"] is None


def test_the_next_question_says_whether_it_is_multi_answer():
    row = round_of()

    assert next_question(row).multi is True

    row.answers = [answer(question_id=row.questions[0]["id"], picks=[0])]

    assert next_question(row).multi is False


def topic(single, multi):
    questions = [{"id": str(uuid4()), "text": "Q?", "options": SINGLE} for _ in range(single)]
    questions += [{"id": str(uuid4()), "text": "Q?", "options": MULTI} for _ in range(multi)]

    return {"id": str(uuid4()), "title": "Ledgers", "questions": questions}


def multi_drawn(content):
    return [
        sum(len(question.options) == len(MULTI) for question in topic.questions)
        for topic in practice_topics(content, 0.1)
    ]


def test_a_practice_round_draws_each_topics_share_of_multi_answer_questions():
    content = {"id": str(uuid4()), "topics": [topic(20, 10), topic(20, 0), topic(0, 20)]}

    # The share where the topic has it; made up with the other kind where it hasn't.
    assert multi_drawn(content) == [
        multi_count(PRACTICE_TOPIC_QUESTIONS, 0.1),
        0,
        PRACTICE_TOPIC_QUESTIONS,
    ]
    assert all(
        len(topic.questions) == PRACTICE_TOPIC_QUESTIONS for topic in practice_topics(content, 0.1)
    )
