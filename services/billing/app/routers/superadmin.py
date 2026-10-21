from fastapi import APIRouter
from prepza_common.stats import Period, StatsOut
from prepza_common.superadmin import SuperadminUser

from app.storage import stats

# The superadmin's stats; everyone else gets "not found".
router = APIRouter(prefix="/superadmin", tags=["superadmin"])


@router.get("/stats")
async def get_stats(superadmin: SuperadminUser, period: Period = None) -> StatsOut:
    """Top-ups, what they paid in each currency and the credits spent, all time or in one year or
    month, for the stats tab."""

    counts, paid = await stats.stats(period)

    return StatsOut(counts=counts, paid=paid)
