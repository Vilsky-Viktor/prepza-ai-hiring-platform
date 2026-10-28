import logging
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, HTTPException, status
from prepza_common.auth.auth import OptionalUser
from prepza_common.auth.superadmin import SuperadminUser, is_superadmin
from prepza_common.limits.maintenance import is_on, put_back_start, set_on, take_start

from companies.integrations import rounds
from companies.integrations.redis import get_redis
from companies.schemas.monitoring import MaintenanceIn, MaintenanceOut, MaintenanceSwitchOut

# Maintenance mode (prepza_common.limits.maintenance): every service reads the switch; it's turned here.
router = APIRouter(tags=["maintenance"])
logger = logging.getLogger(__name__)


@router.get("/maintenance")
async def get_maintenance(user: OptionalUser) -> MaintenanceOut:
    """Public: every page shows the maintenance screen while it's on, except to superadmins."""
    on = await is_on(get_redis())

    return MaintenanceOut(on=on, superadmin=on and user is not None and is_superadmin(user))


async def running() -> int | None:
    """The switch must work even while rounds is down."""
    try:
        return await rounds.running_interviews()
    except httpx.HTTPError:
        logger.warning("Couldn't count the running interviews", exc_info=True)

        return None


@router.get("/superadmin/maintenance")
async def get_switch(superadmin: SuperadminUser) -> MaintenanceSwitchOut:
    return MaintenanceSwitchOut(on=await is_on(get_redis()), running=await running())


async def give_time_back(redis) -> None:
    """Before it turns off, running interviews get back the time it was on. If rounds fails, it
    stays on (a 502) and turning it off again gives the time back."""
    started = await take_start(redis)

    if started is None:
        return

    try:
        await rounds.give_time_back(datetime.now(UTC) - started)
    except httpx.HTTPError:
        logger.exception("Couldn't give running interviews their time back")
        await put_back_start(redis, started)

        raise HTTPException(status.HTTP_502_BAD_GATEWAY) from None


@router.put("/superadmin/maintenance")
async def switch(body: MaintenanceIn, superadmin: SuperadminUser) -> MaintenanceSwitchOut:
    """Who switched it and when goes to the logs."""
    redis = get_redis()

    if not body.on:
        await give_time_back(redis)

    await set_on(redis, body.on, superadmin.uid)

    return MaintenanceSwitchOut(on=body.on, running=await running())
