from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from testee_common.auth.user import UserEmailIn

from library.api.dependencies import ServiceCaller
from library.services.user_data import export_data

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> dict:
    """Accounts, for "Download my data": the user's votes and reports on questions."""
    return jsonable_encoder(await export_data(user_id))
