from datetime import UTC, datetime

from fastapi import HTTPException, status

from rounds.constants.events import ANSWER_RECORDED
from rounds.constants.rounds import CORRECT_SCORE, TIME_UP, RoundStatus
from rounds.helpers.rounds import correct_indexes, find_question
from rounds.helpers.scores import answer_score, picked_options
from rounds.helpers.sessions import answer_seconds, next_session_question
from rounds.models.answers import Answer
from rounds.models.sessions import Session
from rounds.repositories import sessions
from rounds.schemas.rounds import AnswerCreate
from rounds.schemas.sessions import SessionAnswerResult
from rounds.services import outbox as outbox_service


def recorded(answer: Answer, question: dict) -> tuple[str, dict]:
    """The event telling library which options were picked and the credit earned, for the
    question's statistics; it's saved with the answer (see storage add_answer) and published
    right after. `option` (the first pick) stays while library may still read only it."""
    options = [question["options"][index]["answer"] for index in picked_options(answer)]

    return (
        ANSWER_RECORDED,
        {
            "question_id": str(answer.question_id),
            "question_text": question["text"],
            "option": options[0],
            "options": options,
            "correct": answer.correct,
            "credit": answer.score / CORRECT_SCORE,
        },
    )


def checked_answer(row, body: AnswerCreate) -> tuple[Answer, dict]:
    """The checked answer to one question of a session, and that question."""
    if row.status != RoundStatus.IN_PROGRESS:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already finished")

    question = find_question(row, str(body.question_id))

    if question is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question not found")

    if any(answer.question_id == body.question_id for answer in row.answers):
        raise HTTPException(status.HTTP_409_CONFLICT, "Question already answered")

    right = correct_indexes(question)
    multi = len(right) > 1
    picked = body.picked()

    # A single-answer question takes one pick; a multi-answer one any ticks.
    if not multi and len(picked) != 1:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Pick one option for this question."
        )

    score = answer_score(right, picked)
    answer = Answer(
        question_id=body.question_id,
        option_index=None if multi else picked[0],
        picks=picked if multi else None,
        correct=score == CORRECT_SCORE,
        score=score,
    )

    return answer, question


async def submit_session_answer(row: Session, body: AnswerCreate) -> SessionAnswerResult:
    """Candidates see whether they were right only when the interview shares results. The same
    pick (or the same ticks) sent again (it was saved, but its reply was lost on the way) is answered as before
    rather than refused, even once it finished the section, so the candidate doesn't think it
    was lost; a different pick for an answered question is still refused."""
    saved = next((item for item in row.answers if item.question_id == body.question_id), None)

    if saved is not None and picked_options(saved) == body.picked():
        return SessionAnswerResult(
            answer_id=saved.id, answered=len(row.answers), total=len(row.questions)
        )

    if row.status != RoundStatus.IN_PROGRESS:
        raise HTTPException(status.HTTP_409_CONFLICT, "This section is finished")

    if any(answer.question_id == body.question_id and answer.timed_out for answer in row.answers):
        raise HTTPException(status.HTTP_409_CONFLICT, TIME_UP)

    shown = next_session_question(row)

    # Only the question on screen, so its clock always runs while it is answered.
    if row.question_shown_at is None or shown is None or shown.question_id != body.question_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "This question isn't open")

    answer, question = checked_answer(row, body)
    answer.session_id = row.id
    answer.seconds = answer_seconds(row.question_shown_at, datetime.now(UTC))

    # A preview's answers say nothing about a question's quality (a talent's later practice
    # rounds are previews too: they repeat questions whose answers were shown).
    event = None if row.preview else recorded(answer, question)

    if not await sessions.add_answer(answer, event):
        raise HTTPException(status.HTTP_409_CONFLICT, "Question already answered")

    # The section's last answer finishes it, and the interview with its last section, at once
    # rather than on the candidate's next step.
    if len(row.answers) + 1 >= len(row.questions):
        await sessions.finish(row.id)

    await outbox_service.flush_quietly()

    return SessionAnswerResult(
        answer_id=answer.id, answered=len(row.answers) + 1, total=len(row.questions)
    )
