from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from prepza_common.auth.user import UserEmailIn

from assistant.api.dependencies import ServiceCaller
from assistant.services import accounts

router = APIRouter(prefix="/internal", tags=["internal"])


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> None:
    """Library, deleting an account: their conversations go, with every message and tool call,
    the actions they hadn't confirmed yet, and their connected AI apps (whose access stops).
    Safe to repeat."""
    await accounts.delete_user(user_id)


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> dict:
    """Library, for "Download my data": their conversations and messages (text, and the ids
    their blocks refer to), and the AI apps they connected (names and dates)."""
    return jsonable_encoder(await accounts.export_user(user_id))
