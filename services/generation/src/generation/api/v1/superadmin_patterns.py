from uuid import UUID

from fastapi import APIRouter, status
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.db.paging import PageParams

from generation.constants.patterns import PatternStatus
from generation.core.db import Session
from generation.repositories import patterns
from generation.schemas.patterns import PatternOut
from generation.services.patterns import review

# The admin zone's patterns tab (Questions): recurring mistakes the weekly job proposed, approved
# or dismissed here. Everyone else gets "not found".
router = APIRouter(prefix="/superadmin/patterns", tags=["superadmin"])


@router.get("")
async def list_patterns(
    superadmin: SuperadminUser,
    page: PageParams,
    status: PatternStatus = PatternStatus.PROPOSED,
) -> list[PatternOut]:
    async with Session() as session:
        found = await patterns.by_status(session, status, page.offset, page.limit)

    return [PatternOut.model_validate(pattern, from_attributes=True) for pattern in found]


@router.post("/{pattern_id}/approve", status_code=status.HTTP_204_NO_CONTENT)
async def approve(pattern_id: UUID, superadmin: SuperadminUser) -> None:
    """A candidate rule now: it's used only once an eval shows it helps."""
    await review(pattern_id, PatternStatus.APPROVED, superadmin.uid)


@router.post("/{pattern_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss(pattern_id: UUID, superadmin: SuperadminUser) -> None:
    """Never used, and kept so the job doesn't propose it again."""
    await review(pattern_id, PatternStatus.DISMISSED, superadmin.uid)
