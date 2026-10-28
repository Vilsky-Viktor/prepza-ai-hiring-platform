from uuid import UUID

import httpx
from fastapi import HTTPException, status

from assistant.constants.chat import CHAT_FAILED, NOT_FOUND
from assistant.integrations import services
from assistant.models.conversations import Conversation
from assistant.repositories import conversations


async def has_access(company_id: UUID, token: str, language: str) -> bool:
    """Whether the user may still see the company, as companies answers them; a 503 when it
    doesn't answer."""
    try:
        response = await services.get("companies", f"/companies/{company_id}", {}, token, language)
    except httpx.HTTPError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, CHAT_FAILED) from None

    if response.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND):
        return False

    if not response.is_success:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, CHAT_FAILED)

    return True


async def open_conversation(
    conversation_id: UUID, user_id: str, token: str, language: str
) -> Conversation:
    """The user's conversation. One about a company they've lost access to (removed from its
    team, or it's gone) is deleted then, and is a 404 like any other that isn't theirs."""
    conversation = await conversations.owned(conversation_id, user_id)

    if conversation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    if conversation.company_id is not None and not await has_access(
        conversation.company_id, token, language
    ):
        await conversations.delete_one(conversation.id)

        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    return conversation
