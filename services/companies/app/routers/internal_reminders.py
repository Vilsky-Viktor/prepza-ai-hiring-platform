from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from prepza_common.db.paging import IdPageParams

from app.constants.notifications import MAX_COMPANIES_PER_CALL
from app.schemas.internal_reminders import (
    CompaniesMembersOut,
    CompanyIdsIn,
    CompanyIdsOut,
    CompanyMembersOut,
    MemberBriefOut,
    UserIdsOut,
    WaitingIn,
    WaitingInterviewOut,
    WaitingInterviewsOut,
)
from app.service_auth import ServiceCaller
from app.services.access import can_edit
from app.storage import email_reminders

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/companies/members")
async def companies_members(body: CompanyIdsIn, caller: ServiceCaller) -> CompaniesMembersOut:
    """Notifications, for its emails to members: the companies of those ids that still exist,
    their names and who joined them, and whether each is an owner or admin."""
    found = await email_reminders.with_members(body.company_ids)

    return CompaniesMembersOut(
        companies=[
            CompanyMembersOut(
                id=company.id,
                name=company.name,
                members=[
                    MemberBriefOut(user_id=member.user_id, editor=can_edit(member))
                    for member in company.members
                    if member.user_id
                ],
            )
            for company in found
        ]
    )


@router.get("/interviews/waiting/companies")
async def waiting_companies(
    ready_after: datetime,
    ready_before: datetime,
    started_after: datetime,
    started_before: datetime,
    caller: ServiceCaller,
    after: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=MAX_COMPANIES_PER_CALL)] = MAX_COMPANIES_PER_CALL,
) -> CompanyIdsOut:
    """Notifications, for its reminders a page at a time: the companies with an interview ready
    between the `ready_` times that nobody was invited to, or one started between the `started_`
    times still waiting for its questions; up to `limit` after `after`, in order."""
    found = await email_reminders.waiting_company_ids(
        (ready_after, ready_before), (started_after, started_before), after, limit
    )

    return CompanyIdsOut(company_ids=found)


@router.post("/interviews/waiting")
async def waiting_interviews(body: WaitingIn, caller: ServiceCaller) -> WaitingInterviewsOut:
    """Notifications, for its reminders: those companies' interviews ready between the `ready_`
    times that nobody was invited to, and those started between the `started_` times still
    waiting for their questions."""
    idle, generating = await email_reminders.waiting_of(
        (body.ready_after, body.ready_before),
        (body.started_after, body.started_before),
        body.company_ids,
    )

    return WaitingInterviewsOut(
        without_candidates=[
            WaitingInterviewOut.model_validate(row, from_attributes=True) for row in idle
        ],
        being_generated=[
            WaitingInterviewOut.model_validate(row, from_attributes=True) for row in generating
        ],
    )


@router.get("/companies/member-ids")
async def company_member_ids(
    caller: ServiceCaller, page: IdPageParams, editors_only: bool = False
) -> UserIdsOut:
    """Notifications, a page at a time: everyone who joined a company, for a campaign to
    companies; with `editors_only`, their owners and admins, for a notice about the data
    processing agreement or a campaign to them."""
    found = await email_reminders.member_ids(page.after, page.limit, editors_only)

    return UserIdsOut(user_ids=found)
