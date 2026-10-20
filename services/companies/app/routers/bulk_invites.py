from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.auth import CurrentUser
from prepza_common.i18n import TemplateError
from prepza_common.limits import limit, record_hit
from prepza_common.names import clean_name

from app.constants.invites import (
    NAME_NEEDS_ONE_EMAIL,
    NO_EMAILS,
    TOO_MANY_EMAILS,
)
from app.helpers.candidate_lists import read_list
from app.helpers.list_files import list_refusal
from app.integrations.redis import get_redis
from app.schemas.invites import BulkInviteIn, BulkInviteOut, LineProblemOut
from app.services import bulk_invites
from app.services import outbox as outbox_service
from app.services.interview_access import interview_for, ready_for_invites

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("/{interview_id}/candidates/bulk")
async def invite_many(interview_id: UUID, body: BulkInviteIn, user: CurrentUser) -> BulkInviteOut:
    """Invites every email in a pasted or uploaded list, one by one as a single invite would,
    with the names the list gives ("Name <email>", "email, Name", or a CSV's name columns), and
    says who was invited and why the others weren't."""
    interview, company, _ = await interview_for(user, interview_id, editor=True)
    interview = await ready_for_invites(interview, user.uid)

    refusal = list_refusal(body.text, body.filename)

    if refusal:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, refusal)

    found, problems = read_list(body.text)
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

    invited, skipped = await bulk_invites.invite_each(interview, company, user, found)
    await outbox_service.flush_quietly()

    return BulkInviteOut(
        invited=invited,
        skipped=skipped,
        problems=[LineProblemOut(line=line, reason=reason) for line, reason in problems],
    )
