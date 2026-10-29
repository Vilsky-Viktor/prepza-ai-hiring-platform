from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from prepza_common.auth.user import UserEmailIn

from site_content.api.dependencies import ServiceCaller
from site_content.services import accounts

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> dict:
    """Accounts, for "Download my data": the contact messages sent from its email that site
    still keeps."""
    return jsonable_encoder(await accounts.export_user(body.email))
