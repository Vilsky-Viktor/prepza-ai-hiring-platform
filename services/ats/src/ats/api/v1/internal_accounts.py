from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from prepza_common.auth.user import UserEmailIn

from ats.api.dependencies import ServiceCaller
from ats.services import accounts

router = APIRouter(prefix="/internal", tags=["internal"])


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> None:
    """Accounts, deleting an account: an ATS's records of them as a candidate go; the ATS
    connections they made stay with their companies, without their id, and each company is
    told they need reconnecting."""
    await accounts.remove_user(user_id, body.email)


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> dict:
    """Accounts, for "Download my data": what ATSs sent about them as a candidate, and the ATS
    connections they made."""
    return jsonable_encoder(await accounts.export_user(user_id, body.email))
