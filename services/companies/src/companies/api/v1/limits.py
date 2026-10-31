from fastapi import APIRouter
from testee_common.auth.auth import CurrentUser
from testee_common.limits.limits import limit

from companies.integrations.redis import get_redis
from companies.schemas.limits import LimitsOut

router = APIRouter(prefix="/limits", tags=["limits"])


@router.get("")
async def get_limits(user: CurrentUser) -> LimitsOut:
    """For any signed-in user: the limits' current values, as edited in the admin zone."""
    return LimitsOut(max_bulk_invites=await limit(get_redis(), "MAX_BULK_INVITES"))
