from datetime import UTC, datetime, timedelta
from uuid import UUID

from prepza_common import outbox
from prepza_common.notifications import NOTIFICATION_REQUESTED
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert

from app.constants.ats import (
    STALE_CLAIM_MINUTES,
    TOPPED_UP_DAYS,
    CandidateStatus,
    ConnectionStatus,
    FailReason,
)
from app.models.ats import AtsCandidate, AtsConnection
from app.models.outbox import OutboxEvent
from app.storage.db import Session
from app.storage.turns import in_turns


async def add(
    connection_id: UUID,
    link_id: UUID,
    interview_id: UUID,
    candidate_id: str,
    email: str,
    name: str | None = None,
) -> AtsCandidate:
    """The ATS's candidate for the interview: saved waiting the first time, the same row when
    the event comes again (or twice at once: the unique key keeps one, with its first name)."""
    query = (
        insert(AtsCandidate)
        .values(
            connection_id=connection_id,
            link_id=link_id,
            interview_id=interview_id,
            candidate_id=candidate_id,
            email=email.lower(),
            name=name,
            status=CandidateStatus.WAITING,
        )
        .on_conflict_do_nothing(index_elements=["connection_id", "candidate_id", "interview_id"])
    )
    existing = select(AtsCandidate).where(
        AtsCandidate.connection_id == connection_id,
        AtsCandidate.candidate_id == candidate_id,
        AtsCandidate.interview_id == interview_id,
    )

    async with Session() as session:
        await session.execute(query)
        await session.commit()

        return await session.scalar(existing)


def _stale():
    """An invite started this long ago and never settled: the server stopped mid-invite."""
    return and_(
        AtsCandidate.status == CandidateStatus.INVITING,
        AtsCandidate.claimed_at < datetime.now(UTC) - timedelta(minutes=STALE_CLAIM_MINUTES),
    )


async def claim(row_id: UUID, statuses: tuple[str, ...]) -> bool:
    """Marks a candidate as being invited, if it's in one of `statuses` or its last invite was
    cut off: of two requests at once, only one gets True and invites."""
    query = (
        update(AtsCandidate)
        .where(AtsCandidate.id == row_id, or_(AtsCandidate.status.in_(statuses), _stale()))
        .values(status=CandidateStatus.INVITING, claimed_at=datetime.now(UTC))
        .returning(AtsCandidate.id)
    )

    async with Session() as session:
        claimed = await session.scalar(query)
        await session.commit()

    return claimed is not None


async def recoverable() -> list[AtsCandidate]:
    """For the recovery job, oldest first, each connection's in turn: the candidates of working
    connections still waiting (left for later, or arrived while the connection was broken), and
    invites cut off midway."""
    working = select(AtsConnection.id).where(AtsConnection.status == ConnectionStatus.CONNECTED)
    query = in_turns(
        (
            AtsCandidate.connection_id.in_(working),
            or_(AtsCandidate.status == CandidateStatus.WAITING, _stale()),
        ),
        AtsCandidate.created_at,
    )

    async with Session() as session:
        return list((await session.scalars(query)).all())


async def not_invited(company_id: UUID, link_id: UUID) -> list[AtsCandidate]:
    """A linked job's candidates that weren't invited, put back to waiting (with their attempts
    reset), with the ones still waiting or whose invite was cut off midway, oldest first; only
    the company's own."""
    owned = select(AtsConnection.id).where(AtsConnection.company_id == company_id)
    mine = (AtsCandidate.link_id == link_id, AtsCandidate.connection_id.in_(owned))
    requeue = (
        update(AtsCandidate)
        .where(*mine, AtsCandidate.status == CandidateStatus.FAILED)
        .values(status=CandidateStatus.WAITING, reason=None, attempts=0)
    )
    query = (
        select(AtsCandidate)
        .where(*mine, or_(AtsCandidate.status == CandidateStatus.WAITING, _stale()))
        .order_by(AtsCandidate.created_at)
    )

    async with Session() as session:
        await session.execute(requeue)
        await session.commit()

        return list((await session.scalars(query)).all())


async def short_of_credits(company_id: UUID) -> list[AtsCandidate]:
    """The company's candidates, from any ATS, that weren't invited for lack of credits: those
    the ATS sent in the last TOPPED_UP_DAYS, for a job still linked, put back to waiting (with
    their attempts reset), oldest first. An unlinked job's (no longer shown) and older ones stay
    as they are."""
    owned = select(AtsConnection.id).where(AtsConnection.company_id == company_id)
    query = (
        update(AtsCandidate)
        .where(
            AtsCandidate.connection_id.in_(owned),
            AtsCandidate.link_id.is_not(None),
            AtsCandidate.created_at >= datetime.now(UTC) - timedelta(days=TOPPED_UP_DAYS),
            AtsCandidate.status == CandidateStatus.FAILED,
            AtsCandidate.reason == FailReason.CREDITS,
        )
        .values(status=CandidateStatus.WAITING, reason=None, attempts=0)
        .returning(AtsCandidate)
    )

    async with Session() as session:
        found = list((await session.scalars(query)).all())
        await session.commit()

    return sorted(found, key=lambda row: row.created_at)


async def postpone(row_id: UUID) -> None:
    """An invite that failed in passing: back to waiting, for the recovery job, one attempt
    more."""
    query = (
        update(AtsCandidate)
        .where(AtsCandidate.id == row_id)
        .values(status=CandidateStatus.WAITING, attempts=AtsCandidate.attempts + 1)
    )

    async with Session() as session:
        await session.execute(query)
        await session.commit()


async def settle(
    row_id: UUID,
    status: str,
    reason: str | None = None,
    invite_id: UUID | None = None,
    notice: dict | None = None,
) -> None:
    """The candidate's outcome, with the company's notification about it in the same
    transaction (the outbox sends it); the first failure's time is kept."""
    query = (
        update(AtsCandidate)
        .where(AtsCandidate.id == row_id)
        .values(status=status, reason=reason, invite_id=invite_id)
    )

    if status == CandidateStatus.FAILED:
        query = query.values(failed_at=func.coalesce(AtsCandidate.failed_at, func.now()))

    async with Session() as session:
        await session.execute(query)

        if notice:
            outbox.add(session, OutboxEvent, NOTIFICATION_REQUESTED, notice)

        await session.commit()


async def waiting(interview_id: UUID) -> list[AtsCandidate]:
    """The candidates waiting for an interview to be ready, oldest first."""
    query = (
        select(AtsCandidate)
        .where(
            AtsCandidate.status == CandidateStatus.WAITING,
            AtsCandidate.interview_id == interview_id,
        )
        .order_by(AtsCandidate.created_at)
    )

    async with Session() as session:
        return list((await session.scalars(query)).all())


async def counts(company_id: UUID) -> dict[UUID, dict[str, int]]:
    """Per linked job of the company: how many candidates are in each status."""
    owned = select(AtsConnection.id).where(AtsConnection.company_id == company_id)
    query = (
        select(AtsCandidate.link_id, AtsCandidate.status, func.count())
        .where(AtsCandidate.connection_id.in_(owned), AtsCandidate.link_id.is_not(None))
        .group_by(AtsCandidate.link_id, AtsCandidate.status)
    )
    found: dict[UUID, dict[str, int]] = {}

    async with Session() as session:
        for link_id, status, count in (await session.execute(query)).all():
            found.setdefault(link_id, {})[status] = count

    return found


async def delete_older_than(before: datetime) -> int:
    """Candidates the ATS sent before `before` go (they hold emails); how many."""
    async with Session() as session:
        result = await session.execute(delete(AtsCandidate).where(AtsCandidate.created_at < before))
        await session.commit()

        return result.rowcount


async def of_email(email: str) -> list[AtsCandidate]:
    """Every candidate row with this email, oldest first: a user's own data."""
    query = (
        select(AtsCandidate)
        .where(AtsCandidate.email == email.lower())
        .order_by(AtsCandidate.created_at)
    )

    async with Session() as session:
        return list((await session.scalars(query)).all())


async def delete_email(email: str) -> None:
    async with Session() as session:
        await session.execute(delete(AtsCandidate).where(AtsCandidate.email == email.lower()))
        await session.commit()


async def delete_candidate(interview_id: UUID, email: str) -> None:
    """The company erased this candidate: the ATS's record of them for that interview goes."""
    query = delete(AtsCandidate).where(
        AtsCandidate.interview_id == interview_id, AtsCandidate.email == email.lower()
    )

    async with Session() as session:
        await session.execute(query)
        await session.commit()
