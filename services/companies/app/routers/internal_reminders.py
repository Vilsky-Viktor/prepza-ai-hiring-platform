from datetime import datetime

from fastapi import APIRouter
from prepza_common.paging import IdPageParams

from app.schemas.internal_reminders import (
    CompaniesMembersOut,
    CompanyIdsIn,
    CompanyMembersOut,
    MemberBriefOut,
    UserIdsOut,
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


@router.get("/interviews/waiting")
async def waiting_interviews(
    ready_after: datetime,
    ready_before: datetime,
    started_after: datetime,
    started_before: datetime,
    caller: ServiceCaller,
) -> WaitingInterviewsOut:
    """Notifications, for its reminders: interviews ready between the `ready_` times that
    nobody was invited to, and interviews started between the `started_` times still waiting
    for their questions."""
    idle = await email_reminders.without_candidates(ready_after, ready_before)
    generating = await email_reminders.being_generated(started_after, started_before)

    return WaitingInterviewsOut(
        without_candidates=[
            WaitingInterviewOut.model_validate(row, from_attributes=True) for row in idle
        ],
        being_generated=[
            WaitingInterviewOut.model_validate(row, from_attributes=True) for row in generating
        ],
    )


@router.get("/companies/editors")
async def company_editors(caller: ServiceCaller, page: IdPageParams) -> UserIdsOut:
    """Notifications, for a notice about the data processing agreement: every owner and admin
    of a company, a page at a time."""
    return UserIdsOut(user_ids=await email_reminders.editor_ids(page.after, page.limit))
