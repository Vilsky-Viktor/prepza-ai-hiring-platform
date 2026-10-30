import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from rounds.constants.events import INTERVIEW_FINISHED, SESSION_SCORED
from rounds.constants.rounds import RoundStatus
from rounds.core.db import Session
from rounds.helpers.scores import final_score, scored
from rounds.helpers.sessions import new_sections
from rounds.models.sessions import Session as RoundSession
from rounds.repositories import sessions
from rounds.schemas.sessions import SessionsCreate


async def finish(session: AsyncSession, section_id: uuid.UUID) -> None:
    """Finishes one section, in the caller's transaction, scored from the answers saved by the
    time it's locked; unanswered questions count as wrong. When it was the interview's last open
    one, the interview.finished event is saved with it, carrying how many answers the candidate
    picked. A section already finished is left as it is."""
    rows = await sessions.lock_invite_sections(session, section_id)
    finishing = next((row for row in rows if row.id == section_id), None)

    if finishing is None or finishing.status != RoundStatus.IN_PROGRESS:
        return

    score = final_score([answer.score for answer in finishing.answers], len(finishing.questions))
    await sessions.mark_finished(session, finishing, score, datetime.now(UTC))

    # A preview says nothing about the questions; nor does a talent's practice round after
    # their first on a template, which is started as one (services/practice.py).
    if not finishing.preview:
        await sessions.add_event(session, SESSION_SCORED, scored(finishing))

    if all(row.status == RoundStatus.FINISHED for row in rows):
        picked = sum(1 for row in rows for answer in row.answers if not answer.timed_out)
        await sessions.add_event(
            session,
            INTERVIEW_FINISHED,
            {"candidate_invite_id": str(finishing.candidate_invite_id), "answered": picked},
        )


async def finish_open(session: AsyncSession, rows: list[RoundSession]) -> None:
    """Finishes each of `rows` still running, in the caller's transaction."""
    for row in rows:
        if row.status == RoundStatus.IN_PROGRESS:
            await finish(session, row.id)


async def start_interview(body: SessionsCreate) -> list[RoundSession]:
    """One section a topic for a candidate invite; the existing ones when it has them."""
    async with Session() as session:
        existing = await sessions.list_for_invite(session, body.candidate_invite_id)

    if existing:
        return existing

    rows = new_sections(
        body.user_id,
        body.candidate_invite_id,
        body.topics,
        body.question_seconds,
        datetime.now(UTC),
        body.preview,
        company_id=body.company_id,
        voice=body.voice,
    )

    try:
        async with Session.begin() as session:
            await sessions.add_all(session, rows)
    except IntegrityError:
        # Another start for the same invite got there first: theirs are the sections.
        async with Session() as session:
            return await sessions.list_for_invite(session, body.candidate_invite_id)

    return rows
