from fastapi import APIRouter, status
from fastapi.encoders import jsonable_encoder
from prepza_common.ai.tracing import tracing_on
from prepza_common.auth.user import UserEmailIn

from app.integrations import trace_retention
from app.schemas.connect import ConnectionOut
from app.service_auth import ServiceCaller
from app.storage import actions, conversations, messages, oauth

router = APIRouter(prefix="/internal", tags=["internal"])


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> None:
    """Library, deleting an account: their conversations go, with every message and tool call,
    the actions they hadn't confirmed yet, and their connected AI apps (whose access stops).
    Safe to repeat."""
    # Their answers' Langfuse traces first: once the messages go, nothing finds them.
    if tracing_on():
        await trace_retention.delete_traces(await conversations.trace_ids_of_user(user_id))

    await conversations.delete_user(user_id)
    await actions.delete_user(user_id)
    await oauth.delete_user(user_id)


@router.post("/users/{user_id}/export")
async def export_user(user_id: str, body: UserEmailIn, caller: ServiceCaller) -> dict:
    """Library, for "Download my data": their conversations and messages (text, and the ids
    their blocks refer to), and the AI apps they connected (names and dates)."""
    connected = [ConnectionOut.model_validate(grant) for grant in await oauth.of_user(user_id)]

    return jsonable_encoder(
        {
            "assistant_conversations": await messages.export(user_id),
            "connected_ai_apps": connected,
        }
    )
