from fastapi import APIRouter
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.db.stats import Period, StatsOut

from billing.core.db import Session
from billing.repositories import stats

# The superadmin's stats; everyone else gets "not found".
router = APIRouter(prefix="/superadmin", tags=["superadmin"])


@router.get("/stats")
async def get_stats(superadmin: SuperadminUser, period: Period = None) -> StatsOut:
    """Top-ups, what they paid in each currency and the credits spent, all time or in one year or
    month, for the stats tab."""
    async with Session() as session:
        counts, paid = await stats.stats(session, period)

    return StatsOut(counts=counts, paid=paid)
