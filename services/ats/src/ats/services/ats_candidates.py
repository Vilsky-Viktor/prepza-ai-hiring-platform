import logging
import time
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from ats.constants.ats import (
    ATS_NAMES,
    INVITE_BATCH,
    MAX_INVITE_ATTEMPTS,
    CandidateStatus,
    ConnectionStatus,
    FailReason,
)
from ats.core.db import Session
from ats.helpers.notifications import ats_not_invited
from ats.integrations import companies
from ats.models.ats import AtsCandidate, AtsConnection
from ats.repositories import ats, ats_candidates
from ats.services import ats as integrations
from ats.services import outbox as outbox_service

logger = logging.getLogger(__name__)

# Why an invite was refused, by the answer it was refused with.
REASONS = {
    status.HTTP_402_PAYMENT_REQUIRED: FailReason.CREDITS,
    status.HTTP_429_TOO_MANY_REQUESTS: FailReason.LIMIT,
    status.HTTP_503_SERVICE_UNAVAILABLE: FailReason.PAUSED,
}


async def key_of(connection: AtsConnection) -> dict | None:
    """The connection's credentials, also while it's broken (its web hooks' secrets still
    count), or None when its key can't be read (then marked broken)."""
    try:
        return await integrations.credentials(connection)
    except HTTPException:
        return None


async def arrived(
    link, connection: AtsConnection, candidate_id: str, email: str, name: str | None = None
) -> None:
    """A candidate the ATS sent for a linked job (with their name, if it sent one): saved once,
    with the event that invites them (invite_arrived), so the web hook is answered at once."""
    async with Session.begin() as session:
        await ats_candidates.add(
            session, connection.id, link.id, link.interview_id, candidate_id, email, name
        )

    await outbox_service.flush_quietly()


async def invite_arrived(data: dict) -> None:
    """ats.candidate_arrived: invites the candidate an ATS's web hook sent, once (invite claims
    them). Companies not answering raises, so Pub/Sub delivers the event again."""
    async with Session() as session:
        row = await ats_candidates.get(session, UUID(data["ats_candidate_id"]))
        connection = await ats.connection_by_id(session, row.connection_id) if row else None

    if connection is None:
        return

    found = await companies.interviews([row.interview_id])
    await invite(row, connection, found.get(row.interview_id))


async def invite(row: AtsCandidate, connection: AtsConnection, interview: dict | None) -> None:
    """Invites the candidate, once: only a waiting or not-invited one, and only the request that
    claims it. An interview still being made, or a broken connection, keeps them waiting (until
    it's ready, or reconnected); a refused invite (credits, limits, the pause) is kept with its
    reason, to retry. One that's gone is left: its interview.deleted event removes the row."""
    if interview is None or not interview["ready"]:
        return

    if connection.status != ConnectionStatus.CONNECTED:
        return

    async with Session.begin() as session:
        claimed = await ats_candidates.claim(
            session, row.id, (CandidateStatus.WAITING, CandidateStatus.FAILED)
        )

    if not claimed:
        return

    try:
        # As if whoever connected the ATS invited them: their email limits apply.
        invite_id = await companies.invite(
            row.interview_id, row.email, connection.created_by, row.name
        )
    except HTTPException as error:
        if error.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_409_CONFLICT):
            await settle(row.id, CandidateStatus.WAITING)

            return

        # Whoever connected the ATS is no longer an owner or admin: an editor reconnects it.
        if error.status_code == status.HTTP_403_FORBIDDEN:
            await integrations.mark_broken(connection)

        await refused(row, connection, interview, REASONS.get(error.status_code, FailReason.OTHER))

        return
    except Exception:
        # Companies failed or didn't answer: the recovery job tries again, and only the last
        # attempt keeps them as not invited, with a notice.
        logger.exception("Couldn't invite ATS candidate %s", row.id)

        if row.attempts + 1 >= MAX_INVITE_ATTEMPTS:
            await refused(row, connection, interview, FailReason.OTHER)
        else:
            async with Session.begin() as session:
                await ats_candidates.postpone(session, row.id)

        return

    await settle(row.id, CandidateStatus.INVITED, invite_id=invite_id)


async def settle(
    row_id: UUID,
    status: str,
    reason: str | None = None,
    invite_id: UUID | None = None,
    notice: dict | None = None,
) -> None:
    """The candidate's outcome, with the company's notification about it, in one transaction.
    An invite that is another ATS row's already (the same person sent by two connections)
    settles this one without it, and the other's results go back."""
    try:
        async with Session.begin() as session:
            await ats_candidates.settle(session, row_id, status, reason, invite_id, notice)
    except IntegrityError:
        async with Session.begin() as session:
            await ats_candidates.settle(session, row_id, status, reason, None, notice)


async def refused(
    row: AtsCandidate, connection: AtsConnection, interview: dict, reason: str
) -> None:
    """Kept as not invited, to retry; the company's members hear why, and from which ATS."""
    name = ATS_NAMES[connection.provider]
    notice = ats_not_invited(
        interview["company_id"],
        connection.provider,
        name,
        interview["title"],
        row.email,
        reason,
        row.name,
    )
    await settle(row.id, CandidateStatus.FAILED, reason, notice=notice)
    await outbox_service.flush_quietly()


async def invite_all(rows: list[AtsCandidate], stop_at: float | None = None) -> None:
    """Invites the candidates whose interviews are ready (read from companies in one call), in
    their order, at most INVITE_BATCH, or until `stop_at` (time.monotonic) for the recovery job,
    so one run ends in time: the rest stay waiting, for the recovery job. Each is claimed
    first, so a run again (a redelivered event) invites nobody twice."""
    found = await companies.interviews({row.interview_id for row in rows})
    ready = [row for row in rows if (found.get(row.interview_id) or {}).get("ready")]

    async with Session() as session:
        connections = await ats.connections_by_ids(session, {row.connection_id for row in ready})

    for row in ready if stop_at else ready[:INVITE_BATCH]:
        if stop_at and time.monotonic() >= stop_at:
            break

        connection = connections.get(row.connection_id)

        if connection is not None:
            await invite(row, connection, found[row.interview_id])


async def invite_waiting(interview_id: UUID) -> None:
    """An interview just became ready: the candidates the ATS sent for it are invited."""
    async with Session() as session:
        rows = await ats_candidates.waiting(session, interview_id)

    await invite_all(rows)


async def retry(company_id: UUID, link_id: UUID) -> None:
    """A linked job's candidates that weren't invited, or whose invite was cut off, are tried
    again (after a top-up, or once the pause is off): a batch now, the rest by the recovery
    job."""
    await ats_candidates.requeue_not_invited(Session, company_id, link_id)

    async with Session() as session:
        rows = await ats_candidates.not_invited(session, company_id, link_id)

    await invite_all(rows)


async def topped_up(company_id: UUID) -> None:
    """The company got credits: its candidates not invited for lack of them are invited, as far
    as the credits go (the rest are kept, with a new notification); a batch now, the rest by
    the recovery job."""
    async with Session.begin() as session:
        rows = await ats_candidates.requeue_short(session, company_id)

    await ats_candidates.requeue_short_rest(Session, company_id)
    await invite_all(rows)
