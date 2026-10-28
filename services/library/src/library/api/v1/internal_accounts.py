from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from prepza_common.auth.user import UserEmailIn

from library.api.dependencies import ServiceCaller
from library.services.user_data import delete_data, export_data

router = APIRouter(prefix="/internal", tags=["internal"])


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> None:
    """Accounts, deleting an account: the votes and reports the user gave on questions as a
    candidate go; safe to repeat."""
    await delete_data(user_id)


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> dict:
    """Accounts, for "Download my data": the user's votes and reports on questions."""
    return jsonable_encoder(await export_data(user_id))
