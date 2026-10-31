from fastapi import APIRouter
from testee_common.auth.superadmin import SuperadminUser
from testee_common.db.stats import Period, StatsOut

from accounts.services import user_stats

# The superadmin's stats; everyone else gets "not found".
router = APIRouter(prefix="/superadmin", tags=["superadmin"])


@router.get("/stats")
async def get_stats(superadmin: SuperadminUser, period: Period = None) -> StatsOut:
    """Users who signed up, all time or in one year or month, for the stats tab."""

    return StatsOut(counts=await user_stats.stats(period))
