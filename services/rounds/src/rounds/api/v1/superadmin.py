from fastapi import APIRouter
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.db.stats import Period, StatsOut

from rounds.core.db import Session
from rounds.repositories import stats

# The superadmin's stats; everyone else gets "not found".
router = APIRouter(prefix="/superadmin", tags=["superadmin"])


@router.get("/stats")
async def get_stats(superadmin: SuperadminUser, period: Period = None) -> StatsOut:
    """Practice rounds, all time or in one year or
    month, for the stats tab."""
    async with Session() as session:
        return StatsOut(counts=await stats.stats(session, period))
