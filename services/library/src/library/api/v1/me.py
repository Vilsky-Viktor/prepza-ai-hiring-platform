from fastapi import APIRouter, Response, status
from fastapi.encoders import jsonable_encoder
from prepza_common.auth.auth import CurrentUser, FreshUser
from prepza_common.auth.superadmin import is_superadmin
from prepza_common.limits.rate_limit import hit_or_skip

from library.integrations.redis import get_redis
from library.schemas.me import MeOut
from library.services.accounts import delete_account, export_account

router = APIRouter()


@router.get("/me")
def me(user: CurrentUser) -> MeOut:
    return MeOut(**user.model_dump(), is_superadmin=is_superadmin(user))


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(user: CurrentUser) -> None:
    """Deletes the account and everything about it. A company the user alone owns goes too."""
    await delete_account(user)


@router.get("/me/export")
async def export_me(user: FreshUser, response: Response) -> dict:
    """Everything prepza holds about the user, as one JSON file to download."""
    # Each export asks every service for the account's data.
    key = f"rate:data-exports:{user.uid}"
    await hit_or_skip(get_redis(), key, "DATA_EXPORTS_PER_HOUR", user_id=user.uid)
    response.headers["Content-Disposition"] = 'attachment; filename="prepza-data.json"'

    return jsonable_encoder(await export_account(user))
