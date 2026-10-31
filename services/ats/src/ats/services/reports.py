import logging
from uuid import UUID

import httpx
from fastapi import HTTPException, status

from ats.config import settings
from ats.constants.ats import ATS_NAMES, NEEDS_AUTHOR, SCORECARD_LINK, ConnectionStatus
from ats.core.db import Session
from ats.helpers.ats import result_comment
from ats.helpers.notifications import ats_cannot_write
from ats.integrations.errors import WriteRefused
from ats.models.ats import AtsCandidate, AtsConnection
from ats.repositories import ats, ats_results
from ats.services import ats as integrations
from ats.services import outbox as outbox_service
from ats.services.ats_candidates import key_of

logger = logging.getLogger(__name__)


async def mark_reported(row_id: UUID) -> None:
    async with Session.begin() as session:
        await ats_results.mark_reported(session, row_id)


async def keep(row_id: UUID, data: dict) -> None:
    async with Session.begin() as session:
        await ats_results.keep(session, row_id, data)


async def write_refused(row: AtsCandidate, connection: AtsConnection, data: dict) -> None:
    """The key reads but can't write: the results are kept, and sent once the company reconnects
    with a key that can; the company is told, once, in the same transaction. The connection keeps
    inviting meanwhile."""
    notice = ats_cannot_write(
        connection.company_id, connection.provider, ATS_NAMES[connection.provider]
    )

    async with Session.begin() as session:
        await ats_results.keep(session, row.id, data)
        await ats.refuse_writes(session, connection.id, notice)

    await outbox_service.flush_quietly()


async def reported(row: AtsCandidate, connection: AtsConnection) -> None:
    """The results went back: a later refusal tells the company again (when one was told), in
    the same transaction."""
    async with Session.begin() as session:
        if connection.write_refused_at is not None:
            await ats.writes_again(session, connection.id)

        await ats_results.mark_reported(session, row.id)


def comment_of(connection: AtsConnection, data: dict) -> str:
    """The comment written in the ATS about the finished candidate."""
    link = SCORECARD_LINK.format(
        site=settings.site_url,
        company_id=data["company_id"],
        interview_id=data["interview_id"],
        invite_id=data["candidate_invite_id"],
    )

    return result_comment(
        data.get("title") or "",
        data.get("grade"),
        data["passed"],
        data["flagged"],
        link,
        # The team's language, as the member who connected the ATS uses testee; else the test's.
        language=connection.language or data.get("language"),
    )


async def claimed(data: dict) -> tuple[AtsCandidate, AtsConnection] | None:
    """The ATS candidate the finished candidate came from, with its connection, once their
    results are claimed (of two events at once, only one gets them); None when there's nothing
    to write: no ATS sent them, no member to write as (given up), or claimed already."""
    async with Session() as session:
        found = await ats_results.for_invite(session, UUID(data["candidate_invite_id"]))

    if found is None:
        return None

    row, connection = found

    # Workable's comments need an author; Greenhouse's notes don't. Without one, nowhere to write.
    if connection.provider in NEEDS_AUTHOR and connection.member_id is None:
        await mark_reported(row.id)

        return None

    async with Session.begin() as session:
        if not await ats_results.claim(session, row.id, data):
            return None

    return found


async def report(data: dict) -> None:
    """A candidate the ATS sent finished (companies' candidate.finished event, or results kept
    earlier): their results go back to the ATS as a comment, once. They're claimed first, so of
    two events at once only one writes. While the connection is broken, or when the ATS fails,
    they're kept (and the claim freed) for the recovery job, and the event is done: a company's
    failing ATS doesn't hold up Pub/Sub for everyone. No member to write as gives up, and so does
    a candidate gone from the ATS. Candidates no ATS sent are ignored."""
    found = await claimed(data)

    if found is None:
        return

    row, connection = found

    if connection.status != ConnectionStatus.CONNECTED or await key_of(connection) is None:
        await keep(row.id, data)

        return

    try:
        await integrations.call(
            connection,
            "comment",
            candidate_id=row.candidate_id,
            member=connection.member_id,
            text=comment_of(connection, data),
        )
    except (HTTPException, httpx.HTTPError) as error:
        # The candidate is gone from the ATS: nowhere to write.
        if isinstance(error, HTTPException) and error.status_code == status.HTTP_404_NOT_FOUND:
            await mark_reported(row.id)

            return

        # A refused key (the connection was marked broken) or a failing ATS: kept for the
        # recovery job.
        logger.warning("Kept the results of ATS candidate %s: %r", row.id, error)
        await keep(row.id, data)

        return
    except WriteRefused:
        logger.warning("Kept the results of ATS candidate %s: the key can't write", row.id)
        await write_refused(row, connection, data)

        return
    except Exception:
        # Anything else: kept too, as the claim would stop the event's redelivery.
        logger.exception("Kept the results of ATS candidate %s", row.id)
        await keep(row.id, data)

        return

    await reported(row, connection)
