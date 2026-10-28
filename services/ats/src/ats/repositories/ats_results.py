from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, or_, select, update

from ats.constants.ats import STALE_CLAIM_MINUTES, ConnectionStatus
from ats.core.db import Session
from ats.models.ats import AtsCandidate, AtsConnection
from ats.repositories.turns import in_turns

# A finished candidate's results going back to the ATS, once (reported_at, set once the ATS took
# them).


def _free():
    """Not being written now: never claimed, or claimed so long ago the write was cut off."""
    stale = datetime.now(UTC) - timedelta(minutes=STALE_CLAIM_MINUTES)

    return or_(AtsCandidate.report_claimed_at.is_(None), AtsCandidate.report_claimed_at < stale)


async def for_invite(invite_id: UUID) -> tuple[AtsCandidate, AtsConnection] | None:
    """The ATS candidate an invite came from, with its connection, until its results went back."""
    query = (
        select(AtsCandidate, AtsConnection)
        .join(AtsConnection, AtsConnection.id == AtsCandidate.connection_id)
        .where(AtsCandidate.invite_id == invite_id, AtsCandidate.reported_at.is_(None))
    )

    async with Session() as session:
        row = (await session.execute(query)).first()

        return tuple(row) if row else None


async def claim(row_id: UUID, data: dict) -> bool:
    """Marks the results as being written, with them (`data`), before they're sent: of two
    events at once, only one gets True and writes to the ATS. If the write is cut off, the
    recovery job finds them once the claim is stale. keep() frees it when they can't go now,
    mark_reported() once they went."""
    query = (
        update(AtsCandidate)
        .where(AtsCandidate.id == row_id, AtsCandidate.reported_at.is_(None), _free())
        .values(
            report_claimed_at=datetime.now(UTC),
            result=data,
            kept_at=func.coalesce(AtsCandidate.kept_at, func.now()),
        )
        .returning(AtsCandidate.id)
    )

    async with Session() as session:
        claimed = await session.scalar(query)
        await session.commit()

    return claimed is not None


async def keep(row_id: UUID, data: dict) -> None:
    """Results that can't go back now (a broken connection, a failing ATS): kept, to send, and
    the claim on them freed."""
    values = {"result": data, "kept_at": datetime.now(UTC), "report_claimed_at": None}
    query = update(AtsCandidate).where(AtsCandidate.id == row_id).values(**values)

    async with Session() as session:
        await session.execute(query)
        await session.commit()


async def unreported() -> list[AtsCandidate]:
    """Kept results of working connections (also ones whose write was cut off), longest kept
    first, each connection's in turn."""
    working = select(AtsConnection.id).where(AtsConnection.status == ConnectionStatus.CONNECTED)
    query = in_turns(
        (
            AtsCandidate.connection_id.in_(working),
            AtsCandidate.result.is_not(None),
            AtsCandidate.reported_at.is_(None),
            _free(),
        ),
        AtsCandidate.kept_at,
    )

    async with Session() as session:
        return list((await session.scalars(query)).all())


async def mark_reported(row_id: UUID) -> None:
    """Their results went back, or have nowhere to go (the candidate is gone from the ATS)."""
    query = (
        update(AtsCandidate)
        .where(AtsCandidate.id == row_id)
        .values(reported_at=datetime.now(UTC), result=None, report_claimed_at=None)
    )

    async with Session() as session:
        await session.execute(query)
        await session.commit()
