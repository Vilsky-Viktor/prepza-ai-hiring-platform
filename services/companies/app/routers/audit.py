from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.db.paging import PageParams
from prepza_common.events.audit_actions import AuditGroup

from app.helpers.audit import audit_event_out
from app.models.companies import Company
from app.schemas.audit import ActionOut, AuditEventOut
from app.services import action_log
from app.services.access import is_owner, require_company
from app.storage import audit

router = APIRouter(prefix="/companies", tags=["companies"])


async def owned_company(user: CurrentUser, company_id: UUID) -> Company:
    company, caller = await require_company(user, company_id)

    if not is_owner(caller):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the owner can see the audit log")

    return company


@router.get("/{company_id}/audit")
async def list_audit_events(
    company_id: UUID, user: CurrentUser, page: PageParams
) -> list[AuditEventOut]:
    """Every action the company's members took, newest first; for the owner only."""
    company = await owned_company(user, company_id)
    rows = await audit.list_for_company(company.id, page.offset, page.limit)

    return [audit_event_out(row) for row in rows]


@router.get("/{company_id}/actions")
async def list_actions(
    company_id: UUID,
    user: CurrentUser,
    page: PageParams,
    member_id: UUID | None = None,
    group: AuditGroup | None = None,
    start: Annotated[datetime | None, Query(alias="from")] = None,
    end: Annotated[datetime | None, Query(alias="to")] = None,
) -> list[ActionOut]:
    """The company's action log, newest first, each action with who took it and what it was
    about; for the owner only. Only one member's (`member_id`, a joined member), one group's, or
    those from `from` and before `to`."""
    company = await owned_company(user, company_id)
    user_id = None

    if member_id is not None:
        member = next((item for item in company.members if item.id == member_id), None)

        if member is None or member.user_id is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")

        user_id = member.user_id

    events = await audit.list_for_company(
        company.id, page.offset, page.limit, user_id, group, start, end
    )

    return await action_log.rows(company.id, events)
