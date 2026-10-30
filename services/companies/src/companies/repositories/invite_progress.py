import uuid
from datetime import UTC, datetime

from prepza_common.events import processed_events
from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from companies.constants.events import CANDIDATE_FINISHED, CANDIDATE_STARTED, CANDIDATE_UNDELIVERED
from companies.constants.invites import NOT_STARTED, InviteStatus
from companies.models.events import ProcessedEvent
from companies.models.invites import CandidateInvite
from companies.repositories import candidate_events, outbox


async def mark_starting(session: AsyncSession, invite_id: uuid.UUID) -> CandidateInvite | None:
    """The invite as it is now, locked, marked as starting (`starting_at`) while not started yet,
    so its extra time and mode are read after any change saved before and no change lands after;
    None when it's gone. A started one is returned as it is."""
    stored = await session.get(
        CandidateInvite, invite_id, with_for_update=True, populate_existing=True
    )

    if stored is not None and stored.status in NOT_STARTED:
        stored.starting_at = datetime.now(UTC)

    return stored


async def clear_starting(
    session: AsyncSession, invite_id: uuid.UUID, starting_at: datetime | None
) -> None:
    """Lifts the mark of the start that set `starting_at`; a later start's mark stays."""
    await session.execute(
        update(CandidateInvite)
        .where(CandidateInvite.id == invite_id, CandidateInvite.starting_at == starting_at)
        .values(starting_at=None)
    )


async def start(
    session: AsyncSession, invite_id: uuid.UUID, user_id: str, name: str | None = None
) -> str | None:
    """Marks the invite in process, an expired one too (a candidate back through the test's
    link), and returns its status before. None when it's gone: revoked meanwhile. `name`, from
    the candidate's verified sign-in, fills a name not known yet; a known one is kept. The row
    is locked, so of two starts at once only the first fills it."""
    stored = await session.get(CandidateInvite, invite_id, with_for_update=True)

    if stored is None:
        return None

    before = stored.status
    stored.user_id = user_id
    stored.name = stored.name or name

    if stored.status in NOT_STARTED:
        stored.status = InviteStatus.IN_PROCESS
        stored.started_at = stored.started_at or datetime.now(UTC)
        # A first start always carries the candidate's pledge (access.refuse_without_pledge).
        stored.pledged_at = stored.pledged_at or datetime.now(UTC)
        await candidate_events.add(session, CANDIDATE_STARTED, stored.id, stored.interview_id)

    return before


async def mark_undelivered(session: AsyncSession, invite_id: uuid.UUID, notice: dict) -> None:
    """Only an unused invite: a candidate who has started got the email after all. The
    company's notification is saved only when the invite changes, so a repeat sends none."""
    marked = await session.scalar(
        update(CandidateInvite)
        .where(
            CandidateInvite.id == invite_id,
            CandidateInvite.status == InviteStatus.INVITED,
        )
        .values(status=InviteStatus.UNDELIVERED, undelivered_at=func.now())
        .returning(CandidateInvite.interview_id)
    )

    if marked is not None:
        outbox.notify(session, notice)
        await candidate_events.add(session, CANDIDATE_UNDELIVERED, invite_id, marked)


async def finish(
    session: AsyncSession,
    invite_id: uuid.UUID,
    grade: int | None,
    flagged: bool,
    notice: dict | None,
    event_id: str | None = None,
    result: dict | None = None,
) -> None:
    """Marks the invite finished (the candidates list may have already) with the candidate's
    grade and integrity flag, and the company's notification and the candidate.finished event
    (`result`), if any: once per event, and none for a candidate erased meanwhile."""
    new = await processed_events.claim(session, ProcessedEvent, event_id)
    # A candidate erased meanwhile (removed, or their account deleted) stays erased.
    updated = await session.scalar(
        update(CandidateInvite)
        .where(CandidateInvite.id == invite_id, CandidateInvite.status != InviteStatus.DELETED)
        .values(
            status=InviteStatus.FINISHED,
            grade=grade,
            flagged=flagged,
            finished_at=func.coalesce(CandidateInvite.finished_at, func.now()),
        )
        .returning(CandidateInvite.id)
    )
    new = new and updated is not None

    if notice and new:
        outbox.notify(session, notice)

    if result and new:
        outbox.add(session, CANDIDATE_FINISHED, result)
