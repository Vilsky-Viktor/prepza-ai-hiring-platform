from uuid import UUID

from fastapi import APIRouter, status
from prepza_common.auth.service_auth import only_from
from prepza_common.auth.user import UserEmailIn
from prepza_common.config.constants import UPDATES_CALLER

from companies.api.dependencies import ServiceCaller
from companies.core.db import Session
from companies.repositories import invites
from companies.schemas.candidate_updates import CandidateUpdatesIn, CandidateUpdatesOut
from companies.schemas.invites import InvitedCompaniesOut
from companies.services import candidate_updates, invite_delivery

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/invites/{invite_id}/undelivered", status_code=status.HTTP_204_NO_CONTENT)
async def invite_undelivered(invite_id: UUID, caller: ServiceCaller) -> None:
    """Notifications reports a bounced or spam-flagged invite email; safe to repeat. The
    company is told."""
    await invite_delivery.undelivered(invite_id)


@router.post("/invites/companies")
async def invited_companies(body: UserEmailIn, caller: ServiceCaller) -> InvitedCompaniesOut:
    """Notifications, for the admin zone's emails tab: the companies that invited the address,
    whose emails to it a superadmin may stop. The address goes in the body, never the query
    string, which request logs record."""
    async with Session() as session:
        return InvitedCompaniesOut(company_ids=await invites.company_ids_for(session, body.email))


@router.post("/candidates/updates")
async def company_candidate_updates(
    body: CandidateUpdatesIn, caller: ServiceCaller
) -> CandidateUpdatesOut:
    """The assistant, for its get_updates tool: each candidate of these companies who started,
    finished or whose invite wasn't delivered after `since` and up to `until`: the newest
    MAX_UPDATES, newest first, and the counts of all."""
    only_from(caller, UPDATES_CALLER)

    return await candidate_updates.updates(body.company_ids, body.since, body.until)
