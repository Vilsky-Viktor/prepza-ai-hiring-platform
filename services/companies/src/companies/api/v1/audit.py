from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from prepza_common.auth.auth import CurrentUser
from prepza_common.db.paging import PageParams
from prepza_common.events.audit_actions import AuditGroup

from companies.constants.audit import LOG_NOT_OWNER
from companies.core.db import Session
from companies.helpers.audit import audit_event_out
from companies.repositories import audit
from companies.schemas.audit import ActionOut, AuditEventOut
from companies.services import action_log
from companies.services.access import require_owner

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/{company_id}/audit")
async def list_audit_events(
    company_id: UUID, user: CurrentUser, page: PageParams
) -> list[AuditEventOut]:
    """Every action the company's members took, newest first; for the owner only."""
    company = await require_owner(user, company_id, LOG_NOT_OWNER)

    async with Session() as session:
        rows = await audit.list_for_company(session, company.id, page.offset, page.limit)

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
    company = await require_owner(user, company_id, LOG_NOT_OWNER)
    user_id = None

    if member_id is not None:
        member = next((item for item in company.members if item.id == member_id), None)

        if member is None or member.user_id is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")

        user_id = member.user_id

    return await action_log.page(company.id, page.offset, page.limit, user_id, group, start, end)
