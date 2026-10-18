import uuid
from datetime import UTC, datetime

from prepza_common import outbox, processed_events
from prepza_common.notifications import NOTIFICATION_REQUESTED
from sqlalchemy import func, update

from app.constants.events import CANDIDATE_FINISHED, CANDIDATE_STARTED, CANDIDATE_UNDELIVERED
from app.constants.invites import NOT_STARTED, InviteStatus
from app.models.events import ProcessedEvent
from app.models.invites import CandidateInvite
from app.models.outbox import OutboxEvent
from app.storage import candidate_events
from app.storage.db import Session


async def start(invite_id: uuid.UUID, user_id: str, name: str | None = None) -> str | None:
    """Marks the invite in process, an expired one too (a candidate back through the test's
    link), and returns its status before. None when it's gone: revoked meanwhile. `name`, from
    the candidate's verified sign-in, fills a name not known yet; a known one is kept. The row
    is locked, so of two starts at once only the first fills it."""
    async with Session() as session:
        stored = await session.get(CandidateInvite, invite_id, with_for_update=True)

        if stored is None:
            return None

        before = stored.status
        stored.user_id = user_id
        stored.name = stored.name or name

        if stored.status in NOT_STARTED:
            stored.status = InviteStatus.IN_PROCESS
            stored.started_at = stored.started_at or datetime.now(UTC)
            await candidate_events.add(session, CANDIDATE_STARTED, stored.id, stored.interview_id)

        await session.commit()

    return before


async def mark_undelivered(invite_id: uuid.UUID, notice: dict) -> None:
    """Only an unused invite: a candidate who has started got the email after all. The
    company's notification is saved only when the invite changes, so a repeat sends none."""
    async with Session() as session:
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
            outbox.add(session, OutboxEvent, NOTIFICATION_REQUESTED, notice)
            await candidate_events.add(session, CANDIDATE_UNDELIVERED, invite_id, marked)

        await session.commit()


async def finish(
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
    async with Session() as session:
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
            outbox.add(session, OutboxEvent, NOTIFICATION_REQUESTED, notice)

        if result and new:
            outbox.add(session, OutboxEvent, CANDIDATE_FINISHED, result)

        await session.commit()
