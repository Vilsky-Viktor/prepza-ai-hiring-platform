from fastapi import APIRouter
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.db.stats import Period, StatsOut
from prepza_common.limits.limit_schemas import BudgetOut

from rounds.integrations.redis import get_redis
from rounds.repositories import stats
from rounds.services import help as help_service

# The superadmin's stats; everyone else gets "not found".
router = APIRouter(prefix="/superadmin", tags=["superadmin"])


@router.get("/stats")
async def get_stats(superadmin: SuperadminUser, period: Period = None) -> StatsOut:
    """Practice rounds, all time or in one year or
    month, for the stats tab."""

    return StatsOut(counts=await stats.stats(period))


@router.get("/budgets")
async def get_budgets(superadmin: SuperadminUser) -> list[BudgetOut]:
    """How much of the help chat's shared daily budgets is used today, for the AI costs tab."""
    return await help_service.budgets(get_redis())
