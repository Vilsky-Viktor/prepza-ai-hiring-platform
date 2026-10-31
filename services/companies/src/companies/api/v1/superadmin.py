from uuid import UUID

from fastapi import APIRouter
from testee_common.auth.superadmin import SuperadminUser
from testee_common.db.paging import PageParams
from testee_common.db.stats import Period, StatsOut

from companies.constants.monitoring import PassRateSort
from companies.core.db import Session
from companies.repositories import stats
from companies.schemas.monitoring import PassRateOut
from companies.services import pass_rates

# The superadmin's monitoring (internal_docs/compliance/post-market-monitoring-plan.md) and stats;
# everyone else gets "not found".
router = APIRouter(prefix="/superadmin", tags=["superadmin"])


@router.get("/pass-rates")
async def list_pass_rates(
    superadmin: SuperadminUser,
    page: PageParams,
    sort: PassRateSort = PassRateSort.PASS_RATE,
    after: UUID | None = None,
) -> list[PassRateOut]:
    """A page after the interview `after` (the last one shown): paged by key, as the list grows
    across every company."""
    return await pass_rates.page(sort == PassRateSort.FINISHED, after, page.limit)


@router.get("/stats")
async def get_stats(superadmin: SuperadminUser, period: Period = None) -> StatsOut:
    """Companies, interviews and candidates, all time or in one year or
    month, for the stats tab."""

    async with Session() as session:
        return StatsOut(counts=await stats.stats(session, period))
