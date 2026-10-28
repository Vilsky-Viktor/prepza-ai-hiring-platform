from datetime import UTC, datetime, timedelta
from uuid import UUID

from prepza_common.db.db import delete_in_batches, update_in_batches
from prepza_common.events import outbox
from prepza_common.events.notifications import NOTIFICATION_REQUESTED
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ats.constants.ats import (
    INVITE_BATCH,
    STALE_CLAIM_MINUTES,
    TOPPED_UP_DAYS,
    CandidateStatus,
    ConnectionStatus,
    FailReason,
)
from ats.constants.events import ATS_CANDIDATE_ARRIVED
from ats.models.ats import AtsCandidate, AtsConnection
from ats.models.outbox import OutboxEvent
from ats.repositories.ats import company_of
from ats.repositories.turns import in_turns


async def get(session: AsyncSession, row_id: UUID) -> AtsCandidate | None:
    return await session.get(AtsCandidate, row_id)


async def add(
    session: AsyncSession,
    connection_id: UUID,
    link_id: UUID,
    interview_id: UUID,
    candidate_id: str,
    email: str,
    name: str | None = None,
) -> AtsCandidate:
    """The ATS's candidate for the interview: saved waiting the first time, with the
    ats.candidate_arrived event that invites them; the same row, and no new event, when the
    web hook comes again (or twice at once: the unique key keeps one, with its first name)."""
    query = (
        insert(AtsCandidate)
        .values(
            connection_id=connection_id,
            company_id=company_of(connection_id),
            link_id=link_id,
            interview_id=interview_id,
            candidate_id=candidate_id,
            email=email.lower(),
            name=name,
            status=CandidateStatus.WAITING,
        )
        .on_conflict_do_nothing(index_elements=["connection_id", "candidate_id", "interview_id"])
        .returning(AtsCandidate.id)
    )
    existing = select(AtsCandidate).where(
        AtsCandidate.connection_id == connection_id,
        AtsCandidate.candidate_id == candidate_id,
        AtsCandidate.interview_id == interview_id,
    )

    made = await session.scalar(query)

    if made is not None:
        outbox.add(session, OutboxEvent, ATS_CANDIDATE_ARRIVED, {"ats_candidate_id": str(made)})

    return await session.scalar(existing)


def _stale():
    """An invite started this long ago and never settled: the server stopped mid-invite."""
    return and_(
        AtsCandidate.status == CandidateStatus.INVITING,
        AtsCandidate.claimed_at < datetime.now(UTC) - timedelta(minutes=STALE_CLAIM_MINUTES),
    )


async def claim(session: AsyncSession, row_id: UUID, statuses: tuple[str, ...]) -> bool:
    """Marks a candidate as being invited, if it's in one of `statuses` or its last invite was
    cut off: of two requests at once, only one gets True and invites."""
    query = (
        update(AtsCandidate)
        .where(AtsCandidate.id == row_id, or_(AtsCandidate.status.in_(statuses), _stale()))
        .values(status=CandidateStatus.INVITING, claimed_at=datetime.now(UTC))
        .returning(AtsCandidate.id)
    )

    return await session.scalar(query) is not None


async def recoverable(session: AsyncSession) -> list[AtsCandidate]:
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

    return list((await session.scalars(query)).all())


# A candidate not invited, put back to waiting with its attempts reset.
REQUEUED = {"status": CandidateStatus.WAITING, "reason": None, "attempts": 0}


def _of_link(company_id: UUID, link_id: UUID) -> tuple:
    """A linked job's candidates, only the company's own."""
    owned = select(AtsConnection.id).where(AtsConnection.company_id == company_id)

    return (AtsCandidate.link_id == link_id, AtsCandidate.connection_id.in_(owned))


async def requeue_not_invited(sessions, company_id: UUID, link_id: UUID) -> None:
    """A linked job's candidates that weren't invited, put back to waiting a batch at a time,
    each batch its own transaction (`sessions` makes them)."""
    failed = AtsCandidate.status == CandidateStatus.FAILED
    await update_in_batches(
        sessions, AtsCandidate, REQUEUED, *_of_link(company_id, link_id), failed
    )


async def not_invited(session: AsyncSession, company_id: UUID, link_id: UUID) -> list[AtsCandidate]:
    """The first INVITE_BATCH of a linked job's candidates waiting or whose invite was cut off
    midway, oldest first: one batch is invited now (invite_all), the rest by the recovery job."""
    query = (
        select(AtsCandidate)
        .where(
            *_of_link(company_id, link_id),
            or_(AtsCandidate.status == CandidateStatus.WAITING, _stale()),
        )
        .order_by(AtsCandidate.created_at)
        .limit(INVITE_BATCH)
    )

    return list((await session.scalars(query)).all())


def _short(company_id: UUID) -> tuple:
    """The company's candidates, from any ATS, that weren't invited for lack of credits: those
    the ATS sent in the last TOPPED_UP_DAYS, for a job still linked. An unlinked job's (no
    longer shown) and older ones stay as they are."""
    owned = select(AtsConnection.id).where(AtsConnection.company_id == company_id)

    return (
        AtsCandidate.connection_id.in_(owned),
        AtsCandidate.link_id.is_not(None),
        AtsCandidate.created_at >= datetime.now(UTC) - timedelta(days=TOPPED_UP_DAYS),
        AtsCandidate.status == CandidateStatus.FAILED,
        AtsCandidate.reason == FailReason.CREDITS,
    )


async def requeue_short(session: AsyncSession, company_id: UUID) -> list[AtsCandidate]:
    """The oldest INVITE_BATCH of them (_short) put back to waiting, with their attempts reset,
    oldest first: to invite now."""
    short = _short(company_id)
    oldest = select(AtsCandidate.id).where(*short).order_by(AtsCandidate.created_at)
    first = (
        update(AtsCandidate)
        .where(AtsCandidate.id.in_(oldest.limit(INVITE_BATCH)), *short)
        .values(REQUEUED)
        .returning(AtsCandidate)
    )
    found = list((await session.scalars(first)).all())

    return sorted(found, key=lambda row: row.created_at)


async def requeue_short_rest(sessions, company_id: UUID) -> None:
    """The rest of them (_short) put back to waiting, for the recovery job, a batch at a time,
    each batch its own transaction (`sessions` makes them)."""
    await update_in_batches(sessions, AtsCandidate, REQUEUED, *_short(company_id))


async def postpone(session: AsyncSession, row_id: UUID) -> None:
    """An invite that failed in passing: back to waiting, for the recovery job, one attempt
    more."""
    query = (
        update(AtsCandidate)
        .where(AtsCandidate.id == row_id)
        .values(status=CandidateStatus.WAITING, attempts=AtsCandidate.attempts + 1)
    )
    await session.execute(query)


async def settle(
    session: AsyncSession,
    row_id: UUID,
    status: str,
    reason: str | None = None,
    invite_id: UUID | None = None,
    notice: dict | None = None,
) -> None:
    """The candidate's outcome, with the company's notification about it in the same
    transaction (the outbox sends it); the first failure's time is kept. An invite that is
    another row's already (unique) raises IntegrityError."""
    query = (
        update(AtsCandidate)
        .where(AtsCandidate.id == row_id)
        .values(status=status, reason=reason, invite_id=invite_id)
    )

    if status == CandidateStatus.FAILED:
        query = query.values(failed_at=func.coalesce(AtsCandidate.failed_at, func.now()))

    await session.execute(query)

    if notice:
        outbox.add(session, OutboxEvent, NOTIFICATION_REQUESTED, notice)


async def waiting(session: AsyncSession, interview_id: UUID) -> list[AtsCandidate]:
    """The first INVITE_BATCH candidates waiting for an interview to be ready, oldest first: one
    batch is invited now, the rest by the recovery job."""
    query = (
        select(AtsCandidate)
        .where(
            AtsCandidate.status == CandidateStatus.WAITING,
            AtsCandidate.interview_id == interview_id,
        )
        .order_by(AtsCandidate.created_at)
        .limit(INVITE_BATCH)
    )

    return list((await session.scalars(query)).all())


async def counts(session: AsyncSession, company_id: UUID) -> dict[UUID, dict[str, int]]:
    """Per linked job of the company: how many candidates are in each status."""
    owned = select(AtsConnection.id).where(AtsConnection.company_id == company_id)
    query = (
        select(AtsCandidate.link_id, AtsCandidate.status, func.count())
        .where(AtsCandidate.connection_id.in_(owned), AtsCandidate.link_id.is_not(None))
        .group_by(AtsCandidate.link_id, AtsCandidate.status)
    )
    found: dict[UUID, dict[str, int]] = {}

    for link_id, status, count in (await session.execute(query)).all():
        found.setdefault(link_id, {})[status] = count

    return found


async def delete_interview_candidates(sessions, interview_id: UUID) -> None:
    """An interview was deleted: the candidates sent for it go, DELETE_BATCH at a time, each
    batch its own transaction (`sessions` makes them). Safe to repeat."""
    await delete_in_batches(sessions, AtsCandidate, AtsCandidate.interview_id == interview_id)


async def delete_older_than(sessions, before: datetime) -> int:
    """Candidates the ATS sent before `before` go (they hold emails), a batch at a time, each
    batch its own transaction (`sessions` makes them); how many."""
    return await delete_in_batches(sessions, AtsCandidate, AtsCandidate.created_at < before)


async def of_email(session: AsyncSession, email: str) -> list[AtsCandidate]:
    """Every candidate row with this email, oldest first: a user's own data."""
    query = (
        select(AtsCandidate)
        .where(AtsCandidate.email == email.lower())
        .order_by(AtsCandidate.created_at)
    )

    return list((await session.scalars(query)).all())


async def delete_email(session: AsyncSession, email: str) -> None:
    await session.execute(delete(AtsCandidate).where(AtsCandidate.email == email.lower()))


async def delete_candidate(session: AsyncSession, interview_id: UUID, email: str) -> None:
    """The company erased this candidate: the ATS's record of them for that interview goes."""
    query = delete(AtsCandidate).where(
        AtsCandidate.interview_id == interview_id, AtsCandidate.email == email.lower()
    )
    await session.execute(query)
