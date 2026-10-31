import logging
import uuid
from datetime import UTC, datetime, timedelta
from time import monotonic

from testee_common.events.analytics import track

from companies.constants.invites import (
    EXPIRIES_PER_BATCH,
    INVITE_EXPIRY_DAYS,
    JOB_RUN_SECONDS,
    NOT_STARTED,
    SETTLE_BATCH,
    InviteStatus,
)
from companies.core.db import Session
from companies.helpers.candidates import finished_result, stored_results
from companies.helpers.notifications import candidate_finished
from companies.integrations import billing, rounds
from companies.repositories import interviews, invite_expiry, invite_progress, invites
from companies.services import outbox as outbox_service

logger = logging.getLogger(__name__)


async def finish(data: dict, event_id: str) -> None:
    """A finished interview charges the company for the candidate if they picked at least one
    answer, and tells it once, with their grade, however often the event comes; one finished
    without an answer gives the credits back. Billing counts each charge or release once too."""
    invite, interview = await invite_and_interview(uuid.UUID(data["candidate_invite_id"]))

    # Removed, or the candidate deleted their account: its credits were settled then.
    if invite is None or invite.status == InviteStatus.DELETED:
        return

    charged = data["answered"] > 0
    key = invite.hold_key

    # The charge first, so rounds being down never holds it up.
    if charged:
        await billing.charge_candidate(key)
    else:
        await billing.release_candidate(key)

    # Raises when rounds doesn't answer, so the event comes again and the company and its ATS
    # get the grade.
    scores = await rounds.invite_scores([invite.id])
    grade, flagged = stored_results(scores.get(str(invite.id)) or {})
    notice = None

    # The company hears of candidates who answered something, with their grade.
    if charged:
        notice = candidate_finished(interview, invite.id, invite.email, grade, invite.name)

    result = finished_result(interview, invite.id, grade, flagged)

    async with Session.begin() as session:
        await invite_progress.finish(session, invite.id, grade, flagged, notice, event_id, result)

    await outbox_service.flush_quietly()
    await track(
        "interview_finished",
        company_id=interview.company_id,
        answered=data["answered"],
        charged=charged,
    )


async def invite_and_interview(invite_id: uuid.UUID) -> tuple:
    """The invite and its interview; (None, None) when the invite is gone."""
    async with Session() as session:
        invite = await invites.get(session, invite_id)
        interview = await interviews.get(session, invite.interview_id) if invite else None

    return invite, interview


async def expire_unstarted() -> int:
    """Daily: invites never started within INVITE_EXPIRY_DAYS of being sent expire, and their
    credits come back. No batch starts JOB_RUN_SECONDS into the run: the rest the next day."""
    before = datetime.now(UTC) - timedelta(days=INVITE_EXPIRY_DAYS)
    stop_at = monotonic() + JOB_RUN_SECONDS
    count = 0

    # Each invite's credits are released before it's marked expired: if billing fails, the
    # rest stay unexpired and the next run tries them again, so no hold is left open.
    while monotonic() < stop_at and (rows := await expiring(before)):
        for invite in rows:
            key = invite.hold_key
            await billing.release_candidate(key)

            async with Session.begin() as session:
                expired = await invite_expiry.mark_expired(session, invite.id, before)

            # Started or sent again since it was read: it keeps its credits after all.
            if not expired:
                await hold_again(invite, key)

        count += len(rows)

    return count


async def expiring(before: datetime) -> list:
    async with Session() as session:
        return await invite_expiry.expiring(session, before, EXPIRIES_PER_BATCH)


async def hold_again(invite, key: str) -> None:
    """Sets aside again the credits of an invite revived while it was expiring; the run goes on
    if billing refuses. One expired meanwhile by an overlapping run (a retried schedule), or
    removed, keeps nothing set aside."""
    try:
        async with Session() as session:
            current = await invites.get(session, invite.id)
            gone = current is None or current.status in (InviteStatus.EXPIRED, InviteStatus.DELETED)
            interview = None if gone else await interviews.get(session, invite.interview_id)

        if gone:
            return

        await billing.hold_candidate(interview.company_id, key)
    except Exception:
        logger.warning("Couldn't hold credits again for invite %s", invite.id, exc_info=True)


async def release_unfinished(rows: list) -> None:
    """Before a candidate's invites lose their email: the ones not finished give their credits
    back."""
    for interview_id, email, status, stored in rows:
        if status in (*NOT_STARTED, InviteStatus.IN_PROCESS):
            await billing.release_candidate(stored)


async def settle_unfinished(interview_id) -> None:
    """Settles the credits of a deleted interview's unfinished invites (settle_removed),
    SETTLE_BATCH at a time."""
    after = None

    while True:
        async with Session() as session:
            rows = await invites.unfinished(session, interview_id, after, SETTLE_BATCH)

        await settle_removed(rows)

        if len(rows) < SETTLE_BATCH:
            return

        after = rows[-1].id


async def settle_removed(rows: list) -> None:
    """Credits of candidates removed before they finished: one who picked at least one answer
    is charged, the others' come back, as when they finish (questions that ran out of time
    don't count). It asks rounds, so it goes before their answers
    are deleted; safe to repeat (a charged candidate stays charged)."""
    started = [row.id for row in rows if row.status == InviteStatus.IN_PROCESS]
    scores = await rounds.invite_scores(started)

    for row in rows:
        key = row.hold_key

        if (scores.get(str(row.id)) or {}).get("picked"):
            await billing.charge_candidate(key)
        else:
            await billing.release_candidate(key)
