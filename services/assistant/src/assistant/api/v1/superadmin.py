from fastapi import APIRouter
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.limits.limit_schemas import BudgetOut

from assistant.integrations.redis import get_redis
from assistant.services import limits

router = APIRouter(tags=["superadmin"])


@router.get("/superadmin/budgets")
async def budgets(_: SuperadminUser) -> list[BudgetOut]:
    """The admin zone's AI costs tab: how much of the assistant's daily budgets for everyone
    (tokens and messages of people whose company never topped up) is used today."""
    return await limits.shared_budgets(get_redis())
