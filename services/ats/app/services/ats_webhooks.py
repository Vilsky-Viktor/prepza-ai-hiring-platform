import json
from uuid import UUID

from fastapi import HTTPException, status
from prepza_common.i18n.names import clean_name

from app.constants.ats import (
    BREEZY_STATUS_UPDATED,
    GREENHOUSE_STAGE_CHANGE,
    RECRUITEE_MOVED,
    RECRUITEE_STAGE_CHANGED,
    TEAMTAILOR_EVENTS,
    WORKABLE_MOVED,
    AtsProvider,
)
from app.helpers.ats import (
    breezy_signed,
    greenhouse_signed,
    recruitee_signed,
    teamtailor_signed,
    workable_signed,
)
from app.services import ats as integrations
from app.services import ats_candidates as flow
from app.storage import ats, ats_links

# The events each ATS's web hook sends: checked as that ATS's, then a candidate who reached a
# linked job's stage is handed to the candidate flow (ats_candidates.arrived). Anything for a job,
# stage or connection that's gone, or another event, is ignored, so the ATS doesn't send it again.
# A broken connection's events still count, checked with the secrets it keeps: the candidate
# waits, and is invited once it's reconnected.


async def receive_workable(link_id: UUID, body: bytes, signature: str) -> None:
    """A Workable event for a linked job: a candidate moved into its stage gets the interview.
    Only events signed with the account's token count; anything for a job or link that's gone,
    or another event, is ignored, so Workable doesn't send it again."""
    found = await ats_links.link(link_id)

    if found is None:
        return

    link, connection = found
    key = await flow.key_of(connection)

    if key is None:
        return

    if not workable_signed(key["token"], body, signature):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed by Workable")

    event = json.loads(body)
    candidate = event.get("data") or {}

    if (
        event.get("event_type") != WORKABLE_MOVED
        or (candidate.get("job") or {}).get("shortcode") != link.job_id
        or not candidate.get("email")
    ):
        return

    await flow.arrived(
        link,
        connection,
        str(candidate["id"]),
        candidate["email"],
        clean_name(candidate.get("name")),
    )


async def receive_greenhouse(connection_id: UUID, body: bytes, signature: str) -> None:
    """A Greenhouse web hook: a candidate whose application moved into a linked job's stage gets
    the interview. Only events signed with the connection's secret key count; Greenhouse's ping,
    other events, and jobs or stages not linked are ignored."""
    connection = await ats.connection_by_id(connection_id)

    if connection is None or connection.provider != AtsProvider.GREENHOUSE:
        return

    key = await flow.key_of(connection)

    if key is None:
        return

    if not greenhouse_signed(key["webhook_secret"], body, signature):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed by Greenhouse")

    event = json.loads(body)
    application = (event.get("payload") or {}).get("application") or {}
    stage = application.get("current_stage") or {}
    candidate = application.get("candidate") or {}
    emails = [item.get("value") for item in candidate.get("email_addresses") or []]

    if event.get("action") != GREENHOUSE_STAGE_CHANGE or not any(emails):
        return

    for job in application.get("jobs") or []:
        link = await ats_links.link_for_job(connection.id, str(job.get("id")))

        # Its stage by id, or by name (which id Greenhouse's web hooks send isn't settled).
        if link and link.stage_id in (str(stage.get("id")), stage.get("name")):
            reference = f"{candidate.get('id')}:{application.get('id')}"
            await flow.arrived(
                link,
                connection,
                reference,
                next(item for item in emails if item),
                clean_name(candidate.get("first_name"), candidate.get("last_name")),
            )


async def receive_teamtailor(connection_id: UUID, body: bytes, signature: str) -> None:
    """A Teamtailor web hook: a candidate whose application is now in a linked job's stage gets
    the interview. Only events signed with the signature key the company saved count (none
    count before it's saved), and only recent ones. The event only says an application changed,
    so the application is read from Teamtailor: its job, stage and candidate as they are now.
    When Teamtailor answers that read with 429 (too many calls), so is the event."""
    connection = await ats.connection_by_id(connection_id)

    if connection is None or connection.provider != AtsProvider.TEAMTAILOR:
        return

    key = await flow.key_of(connection)

    if key is None:
        return

    if not key.get("webhook_secret") or not teamtailor_signed(
        key["webhook_secret"], body, signature
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed by Teamtailor")

    event = json.loads(body)
    # The event comes on its own, or inside a "payload" envelope.
    event = event.get("payload") or event
    changed = event.get("data") or {}

    if event.get("event_name") not in TEAMTAILOR_EVENTS or not changed.get("id"):
        return

    # Teamtailor sends every application's changes: read only while a job is linked.
    if not await ats_links.has_links(connection.id):
        return

    found = await integrations.call(connection, "application", application_id=str(changed["id"]))
    link = await ats_links.link_for_job(connection.id, found["job_id"] or "")

    if link and link.stage_id == found["stage_id"] and found["email"]:
        await flow.arrived(
            link, connection, found["candidate_id"], found["email"], found.get("name")
        )


async def receive_recruitee(connection_id: UUID, body: bytes, signature: str) -> None:
    """A Recruitee web hook: a candidate moved into a linked job's stage gets the interview. Only
    events signed with the secret the company saved count. Before it's saved, events (Recruitee's
    test when the web hook is created among them) are answered and ignored: the secret is only
    shown once the web hook exists."""
    connection = await ats.connection_by_id(connection_id)

    if connection is None or connection.provider != AtsProvider.RECRUITEE:
        return

    key = await flow.key_of(connection)

    if key is None or not key.get("webhook_secret"):
        return

    if not recruitee_signed(key["webhook_secret"], body, signature):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed by Recruitee")

    event = json.loads(body)
    payload = event.get("payload") or {}
    candidate = payload.get("candidate") or {}
    stage = (payload.get("details") or {}).get("to_stage") or {}
    emails = [email for email in candidate.get("emails") or [] if email]

    if (
        event.get("event_type") != RECRUITEE_MOVED
        or event.get("event_subtype") != RECRUITEE_STAGE_CHANGED
        or not emails
    ):
        return

    link = await ats_links.link_for_job(connection.id, str((payload.get("offer") or {}).get("id")))

    if link and link.stage_id == str(stage.get("id")):
        await flow.arrived(
            link, connection, str(candidate["id"]), emails[0], clean_name(candidate.get("name"))
        )


async def receive_breezy(connection_id: UUID, body: bytes, signature: str) -> None:
    """Breezy HR's web hook, created when connecting: a candidate moved into a linked position's
    stage gets the interview. Only events signed with the secret Breezy gave then count."""
    connection = await ats.connection_by_id(connection_id)

    if connection is None or connection.provider != AtsProvider.BREEZY:
        return

    key = await flow.key_of(connection)

    if key is None or not key.get("webhook_secret"):
        return

    if not breezy_signed(key["webhook_secret"], body, signature):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed by Breezy HR")

    event = json.loads(body)
    found = event.get("object") or {}
    position = found.get("position") or {}
    candidate = found.get("candidate") or {}

    if event.get("type") != BREEZY_STATUS_UPDATED or not candidate.get("email_address"):
        return

    link = await ats_links.link_for_job(connection.id, str(position.get("_id")))

    if link and link.stage_id == str((found.get("stage") or {}).get("id")):
        reference = f"{position['_id']}:{candidate.get('_id')}"
        await flow.arrived(
            link,
            connection,
            reference,
            candidate["email_address"],
            clean_name(candidate.get("name")),
        )
