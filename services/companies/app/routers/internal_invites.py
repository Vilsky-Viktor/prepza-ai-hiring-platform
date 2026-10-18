from uuid import UUID

from fastapi import APIRouter, status
from prepza_common.constants import UPDATES_CALLER
from prepza_common.service_auth import only_from
from prepza_common.user import UserEmailIn

from app.helpers import notifications
from app.helpers.candidate_updates import candidate_updates
from app.schemas.candidate_updates import CandidateUpdatesIn, CandidateUpdatesOut
from app.schemas.invites import InvitedCompaniesOut
from app.service_auth import ServiceCaller
from app.services import outbox as outbox_service
from app.storage import candidate_updates as updates_storage
from app.storage import interviews, invite_progress, invites

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/invites/{invite_id}/undelivered", status_code=status.HTTP_204_NO_CONTENT)
async def invite_undelivered(invite_id: UUID, caller: ServiceCaller) -> None:
    """Notifications reports a bounced or spam-flagged invite email; safe to repeat. The
    company is told."""
    invite = await invites.get(invite_id)

    if invite is None:
        return

    interview = await interviews.get(invite.interview_id)
    await invite_progress.mark_undelivered(
        invite_id,
        notifications.invite_undelivered(interview, str(invite_id), invite.email, invite.name),
    )
    await outbox_service.flush_quietly()


@router.post("/invites/companies")
async def invited_companies(body: UserEmailIn, caller: ServiceCaller) -> InvitedCompaniesOut:
    """Notifications, for the admin zone's emails tab: the companies that invited the address,
    whose emails to it a superadmin may stop. The address goes in the body, never the query
    string, which request logs record."""
    return InvitedCompaniesOut(company_ids=await invites.company_ids_for(body.email))


@router.post("/candidates/updates")
async def company_candidate_updates(
    body: CandidateUpdatesIn, caller: ServiceCaller
) -> CandidateUpdatesOut:
    """The assistant, for its get_updates tool: each candidate of these companies who started,
    finished or whose invite wasn't delivered after `since` and up to `until`, newest first."""
    only_from(caller, UPDATES_CALLER)
    rows = await updates_storage.changed(body.company_ids, body.since, body.until)

    return CandidateUpdatesOut(items=candidate_updates(rows, body.since, body.until))
