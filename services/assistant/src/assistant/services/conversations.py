from uuid import UUID

import httpx
from fastapi import HTTPException, status
from prepza_common.ai.answer_votes import mirror_vote

from assistant.constants.chat import CHAT_FAILED, NOT_FOUND
from assistant.core.db import Session
from assistant.integrations import services
from assistant.models.conversations import Conversation
from assistant.repositories import conversations, messages


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
    async with Session() as session:
        conversation = await conversations.owned(session, conversation_id, user_id)

    if conversation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    if conversation.company_id is not None and not await has_access(
        conversation.company_id, token, language
    ):
        async with Session.begin() as session:
            await conversations.delete_one(session, conversation.id)

        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    return conversation


async def delete_conversation(conversation_id: UUID, user_id: str) -> None:
    """The user's own conversation goes, with its messages; a 404 for one that isn't theirs."""
    async with Session.begin() as session:
        if await conversations.owned(session, conversation_id, user_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

        await conversations.delete_one(session, conversation_id)


async def vote(conversation_id: UUID, user_id: str, message_id: UUID, value: int | None) -> None:
    """The user's vote on an answer in their own conversation (a 404 otherwise), then sent on to
    Langfuse, after it's saved."""
    async with Session.begin() as session:
        found, trace_id = await messages.set_vote(
            session, conversation_id, user_id, message_id, value
        )

    if not found:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    await mirror_vote(trace_id, lambda: vote_of(message_id))


async def vote_of(message_id: UUID) -> int | None:
    """The answer's vote as saved now."""
    async with Session() as session:
        return await messages.vote_of(session, message_id)


async def delete_company(company_id: UUID) -> int:
    """Every conversation about the deleted company, a batch at a time; how many went."""
    return await conversations.delete_company(Session, company_id)


async def delete_mentioning(company_id: UUID, needles: list[str]) -> int:
    """The company's conversations that mention any of `needles` (an erased candidate, a
    deleted interview), a batch at a time; how many went."""
    return await conversations.delete_mentioning(Session, company_id, needles)
