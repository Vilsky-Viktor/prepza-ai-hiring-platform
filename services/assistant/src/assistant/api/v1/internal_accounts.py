from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from testee_common.auth.user import UserEmailIn

from assistant.api.dependencies import ServiceCaller
from assistant.services import accounts

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> dict:
    """Accounts, for "Download my data": their conversations and messages (text, and the ids
    their blocks refer to), and the AI apps they connected (names and dates)."""
    return jsonable_encoder(await accounts.export_user(user_id))
