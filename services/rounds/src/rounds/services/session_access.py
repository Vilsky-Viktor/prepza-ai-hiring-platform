from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from prepza_common.auth.user import User
from sqlalchemy.exc import IntegrityError

from rounds.constants.rounds import RoundStatus
from rounds.core.db import Session
from rounds.helpers.sessions import next_session_question, time_is_up
from rounds.models.answers import Answer
from rounds.models.sessions import Session as RoundSession
from rounds.repositories import sessions
from rounds.services import outbox as outbox_service
from rounds.services import sections
from rounds.services.session_expiry import finish_if_expired


async def read(session_id: UUID) -> RoundSession | None:
    """The section as it is now, with its answers."""
    async with Session() as session:
        return await sessions.get(session, session_id)


async def own_sections(row: RoundSession) -> list[RoundSession]:
    """The sections of `row`'s interview, the candidate's own, in order."""
    async with Session() as session:
        rows = await sessions.list_for_invite(session, row.candidate_invite_id)

    return [item for item in rows if item.user_id == row.user_id]


async def get_own_session(session_id: UUID, user: User) -> RoundSession:
    """The candidate's own session, as it is: for requests on the side of the interview (rating
    or reporting a question, a page leave), which must never time out the question on screen, or
    an answer picked in its last moment would arrive after that and count as wrong."""
    row = await read(session_id)

    if row is None or row.user_id != user.uid:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")

    return row


async def time_out(row: RoundSession) -> bool:
    """The question on screen ran out of time, even with the tab closed: it counts as wrong, and
    when it was the section's last, the section finishes with it, as after a last answer. One
    save: a time-out is never kept without the finish it brings. Whether the section finished;
    False too when another request timed out the same question at once (it did both)."""
    question = next_session_question(row)

    try:
        async with Session.begin() as session:
            if question:
                timed_out = Answer(
                    session_id=row.id,
                    question_id=question.question_id,
                    option_index=None,
                    timed_out=True,
                    correct=False,
                    score=0,
                    seconds=question.seconds,
                )
                await sessions.add_answer(session, timed_out)

            current = await sessions.get(session, row.id)

            if current.status != RoundStatus.IN_PROGRESS or next_session_question(current):
                return False

            await sections.finish(session, row.id)
    except IntegrityError:
        return False

    return True


async def get_owned_session(session_id: UUID, user: User, grace_seconds: int = 0) -> RoundSession:
    """The candidate's own session, brought up to date for the interview's own steps: a question
    whose time ran out counts as wrong, and an interview whose time ran out is finished."""
    row = await get_own_session(session_id, user)

    if row.status == RoundStatus.IN_PROGRESS and time_is_up(row, datetime.now(UTC), grace_seconds):
        if await time_out(row):
            await outbox_service.flush_quietly()

        row = await read(session_id)

    # The whole interview ran out of time while the candidate was away: it's finished.
    if row.status == RoundStatus.IN_PROGRESS and await finish_if_expired(row.candidate_invite_id):
        row = await read(session_id)

    return row
