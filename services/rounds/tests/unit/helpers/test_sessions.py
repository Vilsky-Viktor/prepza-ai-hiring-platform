from datetime import UTC, datetime
from uuid import uuid4

from rounds.helpers.sessions import session_out, topic_out
from rounds.models.sessions import Session


def session(answers=None, final=80):
    return Session(
        id=uuid4(),
        user_id="cand",
        topic_id=uuid4(),
        interview_set_id=uuid4(),
        candidate_invite_id=uuid4(),
        topic_title="Python",
        status="finished",
        questions=[{}, {}],
        final_score=final,
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        answers=answers or [],
    )


def test_candidates_never_see_their_scores():
    shown = session_out(session()).model_dump()

    assert "final_score" not in shown
    assert "current_score" not in shown
    assert "passed" not in shown


def test_topic_out_counts_questions():
    row = session()
    topic = topic_out(row)

    assert topic.topic_title == "Python"
    assert topic.total == 2
    assert topic.answered == 0


def test_the_data_export_shows_right_and_wrong_only_for_practice():
    from rounds.helpers.export import answer_export
    from rounds.models.answers import Answer

    question_id = uuid4()
    questions = [{"id": str(question_id), "text": "Q?", "options": [{"answer": "A"}]}]
    answer = Answer(question_id=question_id, option_index=0, correct=True)

    assert "correct" not in answer_export(questions, answer, practice=False)
    assert answer_export(questions, answer, practice=True)["correct"] is True
