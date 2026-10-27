import uuid

from prepza_common.ai.multi_answer import multi_count

from app.helpers.interviews import pick_questions
from app.schemas.scorecards import ScorecardSection

SINGLE = [{"answer": "a", "correct": True}, {"answer": "b", "correct": False}]
MULTI = [
    {"answer": "a", "correct": True},
    {"answer": "b", "correct": True},
    {"answer": "c", "correct": False},
    {"answer": "d", "correct": False},
]


def questions(single, multi):
    return [{"id": str(uuid.uuid4()), "options": SINGLE} for _ in range(single)] + [
        {"id": str(uuid.uuid4()), "options": MULTI} for _ in range(multi)
    ]


def multi_picked(picked):
    return sum(question["options"] is MULTI for question in picked)


def test_each_candidate_gets_the_topics_share_of_multi_answer_questions():
    picked = pick_questions(questions(50, 20), 20, 0.1)

    assert len(picked) == 20
    assert multi_picked(picked) == multi_count(20, 0.1)


def test_a_topic_short_of_one_kind_makes_up_with_the_other():
    assert multi_picked(pick_questions(questions(50, 0), 20, 0.1)) == 0
    assert multi_picked(pick_questions(questions(5, 30), 20, 0.1)) == 15


def test_a_scorecard_shows_what_a_multi_answer_answer_ticked():
    question = {
        "question_id": str(uuid.uuid4()),
        "number": 1,
        "text": "Which are assets?",
        "options": ["a", "b", "c", "d"],
        "multi": True,
        "correct_option_index": None,
        "correct_indexes": [0, 1],
        "answer": {
            "answer_id": str(uuid.uuid4()),
            "option_index": None,
            "picks": [0, 2],
            "timed_out": False,
            "right_picks": 1,
            "wrong_picks": 1,
            "correct": False,
            "score": 0,
            "seconds": 12,
            "fast": False,
        },
    }
    section = {
        "id": str(uuid.uuid4()),
        "topic_title": "Ledgers",
        "status": "finished",
        "final_score": 0,
        "tab_leaves": 0,
        "copies": 0,
        "fast_answers": 0,
        "review": [question],
        "passed": False,
    }

    [shown] = ScorecardSection.model_validate(section).model_dump(mode="json")["review"]

    assert {key: shown[key] for key in question if key != "answer"} == {
        key: value for key, value in question.items() if key != "answer"
    }
    assert {key: shown["answer"][key] for key in question["answer"]} == question["answer"]
