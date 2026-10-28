from fastapi import APIRouter, status
from prepza_common.auth.superadmin import SuperadminUser

from billing.constants.usage import CHANGES_SHOWN
from billing.core.db import Session
from billing.repositories import limit_settings
from billing.schemas.limits import LimitChangeOut, LimitIn, LimitsOut
from billing.services import limit_values

# Every limit, edited in the admin zone's Controls tab; everyone else gets "not found".
router = APIRouter(prefix="/superadmin/limits", tags=["superadmin"])


@router.get("")
async def get_limits(superadmin: SuperadminUser) -> LimitsOut:
    return await limit_values.limits_out()


@router.get("/changes")
async def get_changes(superadmin: SuperadminUser) -> list[LimitChangeOut]:
    """The latest changes, newest first."""
    async with Session() as session:
        rows = await limit_settings.changes(session, CHANGES_SHOWN)

    return [LimitChangeOut.model_validate(row, from_attributes=True) for row in rows]


@router.put("/{name}")
async def set_limit(name: str, body: LimitIn, superadmin: SuperadminUser) -> LimitsOut:
    """A value out of the limit's bounds is refused (422)."""
    await limit_values.change(name, body.value, superadmin)

    return await limit_values.limits_out()


@router.delete("/{name}", status_code=status.HTTP_200_OK)
async def reset_limit(name: str, superadmin: SuperadminUser) -> LimitsOut:
    await limit_values.change(name, None, superadmin)

    return await limit_values.limits_out()
