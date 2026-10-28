from uuid import UUID

from fastapi import APIRouter, Request, Response, status
from prepza_common.db.paging import PageParams
from prepza_common.i18n.i18n import request_language

from assistant.api.dependencies import UserWithToken
from assistant.constants.chat import RESTORE_MINUTES
from assistant.core.db import Session
from assistant.repositories import conversations
from assistant.schemas.conversations import (
    ConversationDetailOut,
    ConversationOut,
    MessagesOut,
    VoteIn,
)
from assistant.services import conversations as conversation_service
from assistant.services.conversation_pages import messages_page
from assistant.services.conversations import open_conversation

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(
    auth: UserWithToken, page: PageParams, company_id: UUID | None = None
) -> list[ConversationOut]:
    """The user's conversations, the latest first; about one company when it's given."""
    user, _ = auth

    async with Session() as session:
        found = await conversations.of_user(session, user.uid, company_id, page.offset, page.limit)

    return [ConversationOut.model_validate(item) for item in found]


@router.get(
    "/active",
    response_model=ConversationOut,
    responses={204: {"description": "No recent conversation"}},
)
async def active_conversation(auth: UserWithToken) -> ConversationOut | Response:
    """The conversation the panel brings back after a reload: the user's latest, if its last
    message is at most RESTORE_MINUTES old; 204 otherwise."""
    user, _ = auth

    async with Session() as session:
        found = await conversations.latest(session, user.uid, RESTORE_MINUTES)

    if found is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return ConversationOut.model_validate(found)


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: UUID, request: Request, auth: UserWithToken
) -> ConversationDetailOut:
    """One of the user's conversations with its latest messages, and whether earlier ones are
    left (GET .../messages). One about a company they can no longer see is deleted, and is a
    404."""
    user, token = auth
    language = request_language(request)
    conversation = await open_conversation(conversation_id, user.uid, token, language)
    page = await messages_page(conversation.id, user.uid, token, language, None)

    return ConversationDetailOut(
        **ConversationOut.model_validate(conversation).model_dump(), **page.model_dump()
    )


@router.get("/{conversation_id}/messages")
async def earlier_messages(
    conversation_id: UUID, before: UUID, request: Request, auth: UserWithToken
) -> MessagesOut:
    """The messages before the message `before` (the earliest shown), a page at a time."""
    user, token = auth
    language = request_language(request)
    conversation = await open_conversation(conversation_id, user.uid, token, language)

    return await messages_page(conversation.id, user.uid, token, language, before)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: UUID, auth: UserWithToken) -> None:
    user, _ = auth
    await conversation_service.delete_conversation(conversation_id, user.uid)


@router.put("/{conversation_id}/messages/{message_id}/vote", status_code=status.HTTP_204_NO_CONTENT)
async def vote(conversation_id: UUID, message_id: UUID, body: VoteIn, auth: UserWithToken) -> None:
    """The user's thumbs up or down on one of the assistant's answers in their own
    conversation, one an answer: a new vote replaces it, null clears it. Sent on to Langfuse
    as a score on the answer's trace when Langfuse is set up."""
    user, _ = auth
    await conversation_service.vote(conversation_id, user.uid, message_id, body.value)
