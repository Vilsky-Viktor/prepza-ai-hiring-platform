from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from prepza_common.auth.user import User

from rounds.constants.rounds import RoundStatus
from rounds.helpers.sessions import next_session_question, time_is_up
from rounds.models.answers import Answer
from rounds.models.sessions import Session
from rounds.repositories import sessions
from rounds.services import outbox as outbox_service
from rounds.services.session_expiry import finish_if_expired


async def get_own_session(session_id: UUID, user: User) -> Session:
    """The candidate's own session, as it is: for requests on the side of the interview (rating
    or reporting a question, a page leave), which must never time out the question on screen, or
    an answer picked in its last moment would arrive after that and count as wrong."""
    row = await sessions.get(session_id)

    if row is None or row.user_id != user.uid:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")

    return row


async def get_owned_session(session_id: UUID, user: User, grace_seconds: int = 0) -> Session:
    """The candidate's own session, brought up to date for the interview's own steps: a question
    whose time ran out counts as wrong, and an interview whose time ran out is finished."""
    row = await get_own_session(session_id, user)

    # The question on screen ran out of time, even with the tab closed: it counts as wrong.
    if row.status == RoundStatus.IN_PROGRESS and time_is_up(row, datetime.now(UTC), grace_seconds):
        question = next_session_question(row)

        if question:
            await sessions.add_answer(
                Answer(
                    session_id=row.id,
                    question_id=question.question_id,
                    option_index=None,
                    timed_out=True,
                    correct=False,
                    score=0,
                    seconds=row.question_seconds,
                )
            )

        row = await sessions.get(session_id)

        # That was the section's last question: it finishes now, as after a last answer.
        if row.status == RoundStatus.IN_PROGRESS and next_session_question(row) is None:
            await sessions.finish(row.id)
            await outbox_service.flush_quietly()
            row = await sessions.get(session_id)

    # The whole interview ran out of time while the candidate was away: it's finished.
    if row.status == RoundStatus.IN_PROGRESS and await finish_if_expired(row.candidate_invite_id):
        row = await sessions.get(session_id)

    return row
