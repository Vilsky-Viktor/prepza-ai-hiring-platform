from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from testee_common.config.constants import REFERRAL_COOKIE
from testee_common.http.sse import event_stream
from testee_common.i18n.i18n import request_language

from assistant.api.dependencies import UserWithToken
from assistant.services import actions, confirmations

router = APIRouter(prefix="/conversations/{conversation_id}/actions", tags=["actions"])


@router.post("/{action_id}/confirm")
async def confirm(
    conversation_id: UUID, action_id: UUID, request: Request, auth: UserWithToken
) -> StreamingResponse:
    """Runs an action the assistant prepared, once, as the user, with exactly the arguments its
    card showed: only the user it was prepared for, in this conversation, about a company that's
    still theirs. Server-sent events like /chat's, after {"action": the card's new state}. A
    second confirm, a cancelled or an expired action is a 409 (or 404); a refused token a 401,
    and the action can be confirmed again with a fresh one."""
    user, token = auth
    language = request_language(request)
    # The referral link the user came through, for a company the action creates.
    referral = request.cookies.get(REFERRAL_COOKIE)

    return event_stream(
        await confirmations.confirm(conversation_id, action_id, user, token, language, referral)
    )


@router.post("/{action_id}/cancel")
async def cancel(
    conversation_id: UUID, action_id: UUID, request: Request, auth: UserWithToken
) -> dict:
    """Drops an action the assistant prepared; nothing runs."""
    user, token = auth

    return await actions.cancel(conversation_id, action_id, user, token, request_language(request))
