import asyncio
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.i18n.i18n import TemplateError
from prepza_common.i18n.names import clean_name
from prepza_common.limits.limits import limit, record_hit

from companies.constants.invites import (
    NAME_NEEDS_ONE_EMAIL,
    NO_EMAILS,
    TOO_MANY_EMAILS,
)
from companies.helpers.candidate_lists import read_list
from companies.helpers.list_files import list_refusal
from companies.integrations.redis import get_redis
from companies.schemas.invites import BulkInviteIn, BulkInviteOut, LineProblemOut
from companies.services import bulk_invites
from companies.services import outbox as outbox_service
from companies.services.interview_access import interview_for, ready_for_invites
from companies.services.voice_modes import refuse_unspoken

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("/{interview_id}/candidates/bulk")
async def invite_many(interview_id: UUID, body: BulkInviteIn, user: CurrentUser) -> BulkInviteOut:
    """Invites every email in a pasted or uploaded list, one by one as a single invite would,
    with the names the list gives ("Name <email>", "email, Name", or a CSV's name columns), and
    says who was invited and why the others weren't. `voice` chooses how they all take it."""
    interview, company, _ = await interview_for(user, interview_id, editor=True)
    interview = await ready_for_invites(interview, user.uid)
    refuse_unspoken(interview, body.voice)

    refusal = list_refusal(body.text, body.filename)

    if refusal:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, refusal)

    # Up to 200,000 characters of parsing: off the event loop.
    found, problems = await asyncio.to_thread(read_list, body.text)
    name = clean_name(body.name)

    if not found and not problems:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NO_EMAILS)

    if name and len(found) + len(problems) > 1:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, NAME_NEEDS_ONE_EMAIL)

    # The form's name field wins over a name in the text.
    if name and found:
        found = [(found[0][0], name)]

    most = await limit(get_redis(), "MAX_BULK_INVITES")

    if len(found) > most:
        await record_hit("MAX_BULK_INVITES", company_id=company.id, user_id=user.uid)

        raise TemplateError(status.HTTP_422_UNPROCESSABLE_CONTENT, TOO_MANY_EMAILS, limit=most)

    invited, skipped = await bulk_invites.invite_each(interview, company, user, found, body.voice)
    await outbox_service.flush_quietly()

    return BulkInviteOut(
        invited=invited,
        skipped=skipped,
        problems=[LineProblemOut(line=line, reason=reason) for line, reason in problems],
    )
