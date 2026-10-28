"""The admin zone's stats from rounds' records."""

from prepza_common.db.stats import counted
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from rounds.models.sessions import Session as RoundSession


async def stats(session: AsyncSession, period: str | None) -> dict[str, int]:
    """All time or in `period` (a year or a period): talents' free practice rounds, in the month each started. A round is
    one session per topic, all with the round's id in candidate_invite_id."""
    rounds = (
        select(func.min(RoundSession.started_at).label("started_at"))
        .where(RoundSession.practice)
        .group_by(RoundSession.candidate_invite_id)
        .subquery()
    )

    return {
        "practice": await counted(
            session, func.count(rounds.c.started_at), rounds.c.started_at, period
        ),
    }
