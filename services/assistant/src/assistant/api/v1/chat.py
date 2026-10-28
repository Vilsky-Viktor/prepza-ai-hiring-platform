from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from prepza_common.http.sse import event_stream
from prepza_common.i18n.i18n import request_language
from prepza_common.limits.limits import limit

from assistant.api.dependencies import UserWithToken
from assistant.constants.chat import MAX_MESSAGE_LENGTH, RESTORE_MINUTES
from assistant.constants.limits import MAX_AUDIO_SECONDS
from assistant.integrations.redis import get_redis
from assistant.schemas.chat import ChatRequest, ConfigOut, WelcomeOut
from assistant.services import turns
from assistant.services.welcome import welcome_stage

router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat(body: ChatRequest, request: Request, auth: UserWithToken) -> StreamingResponse:
    """A message to the assistant, which answers from the services' data the user may read, in
    the interface's language. Server-sent events: {"conversation": {"id"}}, then any of
    {"tool": {"name", "state", "label"}}, {"block"} and {"delta"}, and last {"done":
    {"message_id"}} or {"error"} ({"code": "session_expired"} when the user's token stopped
    working: refresh it and send again); a keep-alive comment every 15 s. Refused before it
    streams during the emergency pause and over a limit."""
    user, token = auth
    events = await turns.start(body, user, token, request_language(request))

    return event_stream(events)


@router.get("/config")
async def config() -> ConfigOut:
    """The limits the panel keeps to; public, as the panel asks it signed out too."""
    redis = get_redis()

    return ConfigOut(
        restore_minutes=RESTORE_MINUTES,
        max_message_length=MAX_MESSAGE_LENGTH,
        max_audio_seconds=MAX_AUDIO_SECONDS,
        messages_per_hour=await limit(redis, "MESSAGES_PER_USER_HOUR"),
        messages_per_day=await limit(redis, "MESSAGES_PER_USER_DAY"),
    )


@router.get("/welcome")
async def welcome(
    request: Request, auth: UserWithToken, company_id: UUID | None = None
) -> WelcomeOut:
    """Where the user is (no company yet, not verified, no interviews, no candidates, or
    candidates), from their companies or the one of the page they're on: the panel's welcome
    says what the assistant can help with there."""
    _, token = auth

    return WelcomeOut(stage=await welcome_stage(company_id, token, request_language(request)))
