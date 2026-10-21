import logging
import time
from uuid import UUID

import httpx
from fastapi import HTTPException, status

from app.config.settings import settings
from app.constants.ats import (
    ATS_NAMES,
    INVITE_BATCH,
    MAX_INVITE_ATTEMPTS,
    NEEDS_AUTHOR,
    RECOVER_INVITE_SECONDS,
    REPORT_SECONDS,
    SCORECARD_LINK,
    CandidateStatus,
    ConnectionStatus,
    FailReason,
)
from app.helpers.ats import (
    result_comment,
)
from app.helpers.notifications import ats_cannot_write, ats_not_invited
from app.integrations import companies
from app.integrations.errors import WriteRefused
from app.models.ats import AtsCandidate, AtsConnection
from app.services import ats as integrations
from app.services import outbox as outbox_service
from app.storage import ats, ats_candidates, ats_results

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
    then invited. When companies doesn't answer, they wait for the recovery job."""
    row = await ats_candidates.add(
        connection.id, link.id, link.interview_id, candidate_id, email, name
    )

    try:
        found = await companies.interviews([row.interview_id])
    except Exception:
        logger.exception("Couldn't read the interview of ATS candidate %s", row.id)

        return

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

    claimed = await ats_candidates.claim(row.id, (CandidateStatus.WAITING, CandidateStatus.FAILED))

    if not claimed:
        return

    try:
        # As if whoever connected the ATS invited them: their email limits apply.
        invite_id = await companies.invite(
            row.interview_id, row.email, connection.created_by, row.name
        )
    except HTTPException as error:
        if error.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_409_CONFLICT):
            await ats_candidates.settle(row.id, CandidateStatus.WAITING)

            return

        # Whoever connected the ATS is no longer an owner or admin: an editor reconnects it.
        if error.status_code == status.HTTP_403_FORBIDDEN:
            await ats.mark_broken(connection.id)
            await outbox_service.flush_quietly()

        await refused(row, connection, interview, REASONS.get(error.status_code, FailReason.OTHER))

        return
    except Exception:
        # Companies failed or didn't answer: the recovery job tries again, and only the last
        # attempt keeps them as not invited, with a notice.
        logger.exception("Couldn't invite ATS candidate %s", row.id)

        if row.attempts + 1 >= MAX_INVITE_ATTEMPTS:
            await refused(row, connection, interview, FailReason.OTHER)
        else:
            await ats_candidates.postpone(row.id)

        return

    await ats_candidates.settle(row.id, CandidateStatus.INVITED, invite_id=invite_id)


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
    await ats_candidates.settle(row.id, CandidateStatus.FAILED, reason, notice=notice)
    await outbox_service.flush_quietly()


async def invite_all(rows: list[AtsCandidate], stop_at: float | None = None) -> None:
    """Invites the candidates whose interviews are ready (read from companies in one call), in
    their order, at most INVITE_BATCH, or until `stop_at` (time.monotonic) for the recovery job,
    so one run ends in time: the rest stay waiting, for the recovery job. Each is claimed
    first, so a run again (a redelivered event) invites nobody twice."""
    found = await companies.interviews({row.interview_id for row in rows})
    ready = [row for row in rows if (found.get(row.interview_id) or {}).get("ready")]
    connections = await ats.connections_by_ids({row.connection_id for row in ready})

    for row in ready if stop_at else ready[:INVITE_BATCH]:
        if stop_at and time.monotonic() >= stop_at:
            break

        connection = connections.get(row.connection_id)

        if connection is not None:
            await invite(row, connection, found[row.interview_id])


async def invite_waiting(interview_id: UUID) -> None:
    """An interview just became ready: the candidates the ATS sent for it are invited."""
    await invite_all(await ats_candidates.waiting(interview_id))


async def retry(company_id: UUID, link_id: UUID) -> None:
    """A linked job's candidates that weren't invited, or whose invite was cut off, are tried
    again (after a top-up, or once the pause is off): a batch now, the rest by the recovery
    job."""
    await invite_all(await ats_candidates.not_invited(company_id, link_id))


async def topped_up(company_id: UUID) -> None:
    """The company got credits: its candidates not invited for lack of them are invited, as far
    as the credits go (the rest are kept, with a new notification); a batch now, the rest by
    the recovery job."""
    await invite_all(await ats_candidates.short_of_credits(company_id))


async def recover() -> int:
    """Every 10 minutes: candidates still waiting (left for later by a run, by companies not
    answering, or sent while the connection was broken) and invites cut off midway (the server
    stopped) are invited, until RECOVER_INVITE_SECONDS into the run; results kept while a
    connection was broken or the ATS failed go back, until REPORT_SECONDS into it. Both go
    through every connection's in turn. How many candidates were found."""
    started = time.monotonic()
    rows = await ats_candidates.recoverable()
    await invite_all(rows, started + RECOVER_INVITE_SECONDS)

    for row in await ats_results.unreported():
        if time.monotonic() >= started + REPORT_SECONDS:
            break

        try:
            await report(row.result)
        except Exception:
            logger.exception("Couldn't send the results of ATS candidate %s", row.id)

    return len(rows)


async def report(data: dict) -> None:
    """A candidate the ATS sent finished (companies' candidate.finished event, or results kept
    earlier): their results go back to the ATS as a comment, once. They're claimed first, so of
    two events at once only one writes. While the connection is broken, or when the ATS fails,
    they're kept (and the claim freed) for the recovery job, and the event is done: a company's
    failing ATS doesn't hold up Pub/Sub for everyone. No member to write as gives up, and so does
    a candidate gone from the ATS. Candidates no ATS sent are ignored."""
    found = await ats_results.for_invite(UUID(data["candidate_invite_id"]))

    if found is None:
        return

    row, connection = found

    # Workable's comments need an author; Greenhouse's notes don't. Without one, nowhere to write.
    if connection.provider in NEEDS_AUTHOR and connection.member_id is None:
        await ats_results.mark_reported(row.id)

        return

    if not await ats_results.claim(row.id, data):
        return

    if connection.status != ConnectionStatus.CONNECTED or await key_of(connection) is None:
        await ats_results.keep(row.id, data)

        return

    link = SCORECARD_LINK.format(
        site=settings.site_url,
        company_id=data["company_id"],
        interview_id=data["interview_id"],
        invite_id=data["candidate_invite_id"],
    )
    text = result_comment(
        data.get("title") or "",
        data.get("grade"),
        data["passed"],
        data["flagged"],
        link,
        # The team's language, as the member who connected the ATS uses prepza; else the test's.
        language=connection.language or data.get("language"),
    )

    try:
        await integrations.call(
            connection,
            "comment",
            candidate_id=row.candidate_id,
            member=connection.member_id,
            text=text,
        )
    except (HTTPException, httpx.HTTPError) as error:
        # The candidate is gone from the ATS: nowhere to write.
        if isinstance(error, HTTPException) and error.status_code == status.HTTP_404_NOT_FOUND:
            await ats_results.mark_reported(row.id)

            return

        # A refused key (the connection was marked broken) or a failing ATS: kept for the
        # recovery job.
        logger.warning("Kept the results of ATS candidate %s: %r", row.id, error)
        await ats_results.keep(row.id, data)

        return
    except WriteRefused:
        # The key reads but can't write: kept, and sent once the company reconnects with a key
        # that can; the connection keeps inviting meanwhile.
        logger.warning("Kept the results of ATS candidate %s: the key can't write", row.id)
        await ats_results.keep(row.id, data)
        notice = ats_cannot_write(
            connection.company_id, connection.provider, ATS_NAMES[connection.provider]
        )
        await ats.refuse_writes(connection.id, notice)
        await outbox_service.flush_quietly()

        return
    except Exception:
        # Anything else: kept too, as the claim would stop the event's redelivery.
        logger.exception("Kept the results of ATS candidate %s", row.id)
        await ats_results.keep(row.id, data)

        return

    if connection.write_refused_at is not None:
        await ats.writes_again(connection.id)

    await ats_results.mark_reported(row.id)
