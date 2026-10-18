import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from prepza_common.paging import PageParams
from prepza_common.superadmin import SuperadminUser

from app.constants.patterns import PatternStatus
from app.schemas.patterns import PatternOut
from app.storage import patterns

logger = logging.getLogger(__name__)

# The admin zone's patterns tab (Questions): recurring mistakes the weekly job proposed, approved
# or dismissed here. Everyone else gets "not found".
router = APIRouter(prefix="/superadmin/patterns", tags=["superadmin"])


@router.get("")
async def list_patterns(
    superadmin: SuperadminUser,
    page: PageParams,
    status: PatternStatus = PatternStatus.PROPOSED,
) -> list[PatternOut]:
    found = await patterns.by_status(status, page.offset, page.limit)

    return [PatternOut.model_validate(pattern, from_attributes=True) for pattern in found]


async def review(pattern_id: UUID, decision: PatternStatus, superadmin) -> None:
    if not await patterns.review(pattern_id, decision, superadmin.uid):
        raise HTTPException(status.HTTP_409_CONFLICT, "This pattern was already reviewed")

    logger.info("Quality pattern %s %s by superadmin %s", pattern_id, decision, superadmin.uid)


@router.post("/{pattern_id}/approve", status_code=status.HTTP_204_NO_CONTENT)
async def approve(pattern_id: UUID, superadmin: SuperadminUser) -> None:
    """A candidate rule now: it's used only once an eval shows it helps."""
    await review(pattern_id, PatternStatus.APPROVED, superadmin)


@router.post("/{pattern_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss(pattern_id: UUID, superadmin: SuperadminUser) -> None:
    """Never used, and kept so the job doesn't propose it again."""
    await review(pattern_id, PatternStatus.DISMISSED, superadmin)
