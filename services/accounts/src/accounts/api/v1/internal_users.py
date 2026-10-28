from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from prepza_common.auth.user import UserEmailIn

from accounts.api.dependencies import ServiceCaller
from accounts.services.user_data import delete_data, export_data

router = APIRouter(prefix="/internal", tags=["internal"])


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> None:
    """Deleting an account: its email settings with their consent log and its accepted terms
    go; safe to repeat."""
    await delete_data(user_id)


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> dict:
    """For "Download my data": the account's email settings, their consent log and the terms
    it accepted."""
    return jsonable_encoder(await export_data(user_id))
