from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from testee_common.auth.user import UserEmailIn

from ats.api.dependencies import ServiceCaller
from ats.services import accounts

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> dict:
    """Accounts, for "Download my data": what ATSs sent about them as a candidate, and the ATS
    connections they made."""
    return jsonable_encoder(await accounts.export_user(user_id, body.email))
