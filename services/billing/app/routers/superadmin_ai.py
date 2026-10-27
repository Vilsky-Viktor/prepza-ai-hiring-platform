from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.db.stats import Period

from app.schemas.ai_costs import AiCostsOut, AiSpendOut
from app.schemas.limits import LimitHitListsOut
from app.services.ai_costs import ai_costs_out, spend_out
from app.services.limit_hit_lists import limit_hits_out

# The admin zone's AI costs tab; everyone else gets "not found".
router = APIRouter(prefix="/superadmin", tags=["superadmin"])


@router.get("/ai-costs")
async def get_ai_costs(superadmin: SuperadminUser, period: Period = None) -> AiCostsOut:
    """What AI cost, all time or in one year or month, and why."""
    return await ai_costs_out(period)


@router.get("/limit-hits")
async def get_limit_hits(superadmin: SuperadminUser, period: Period = None) -> LimitHitListsOut:
    return await limit_hits_out(period)


@router.get("/ai-spend")
async def get_ai_spend(
    superadmin: SuperadminUser, company_id: str | None = None, user_id: str | None = None
) -> AiSpendOut:
    """One company's or user's AI spend lately, for its support page."""
    if not company_id and not user_id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Name a company or a user")

    return await spend_out(company_id, user_id)
