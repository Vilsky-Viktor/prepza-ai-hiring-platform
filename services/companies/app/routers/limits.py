from fastapi import APIRouter
from prepza_common.auth.auth import CurrentUser
from prepza_common.limits.limits import limit

from app.integrations.redis import get_redis
from app.schemas.limits import LimitsOut

router = APIRouter(prefix="/limits", tags=["limits"])


@router.get("")
async def get_limits(user: CurrentUser) -> LimitsOut:
    """For any signed-in user: the limits' current values, as edited in the admin zone."""
    return LimitsOut(max_bulk_invites=await limit(get_redis(), "MAX_BULK_INVITES"))
