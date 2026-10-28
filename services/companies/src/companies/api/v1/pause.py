from fastapi import APIRouter
from prepza_common.auth.superadmin import SuperadminUser
from prepza_common.limits.pause import is_paused, set_paused

from companies.integrations.redis import get_redis
from companies.schemas.monitoring import PauseIn, PauseOut

# The emergency pause (prepza_common.limits.pause): every service reads the switch; it's turned here.
router = APIRouter(tags=["pause"])


@router.get("/pause")
async def get_pause() -> PauseOut:
    """Public: the candidate's invite page and the new interview page say so while it's on."""
    return PauseOut(paused=await is_paused(get_redis()))


@router.put("/superadmin/pause")
async def switch_pause(body: PauseIn, superadmin: SuperadminUser) -> PauseOut:
    """Who switched it and when goes to the logs."""
    await set_paused(get_redis(), body.paused, superadmin.uid)

    return PauseOut(paused=body.paused)
