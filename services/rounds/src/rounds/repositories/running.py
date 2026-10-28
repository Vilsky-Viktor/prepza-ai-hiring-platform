from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from rounds.constants.maintenance import RUNNING_WINDOW
from rounds.constants.rounds import RoundStatus
from rounds.models.sessions import Session


async def running_interviews(session: AsyncSession) -> int:
    """Candidates' interviews with a question on screen now; previews and practice rounds stay
    out."""
    query = select(func.count(func.distinct(Session.candidate_invite_id))).where(
        Session.status == RoundStatus.IN_PROGRESS,
        ~Session.preview,
        ~Session.practice,
        Session.question_shown_at > datetime.now(UTC) - RUNNING_WINDOW,
    )

    return await session.scalar(query)


async def give_time_back(session: AsyncSession, stopped: timedelta) -> None:
    """Moves running interviews' clocks on by `stopped`: every section's start, as the interview's
    deadline counts from the first one (session_expiry.py), and the shown time of the question
    on screen, which its own deadline counts from."""
    running = select(Session.candidate_invite_id).where(Session.status == RoundStatus.IN_PROGRESS)

    await session.execute(
        update(Session)
        .where(Session.candidate_invite_id.in_(running))
        .values(started_at=Session.started_at + stopped)
    )
    await session.execute(
        update(Session)
        .where(Session.status == RoundStatus.IN_PROGRESS, Session.question_shown_at.is_not(None))
        .values(question_shown_at=Session.question_shown_at + stopped)
    )
