from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response, status
from prepza_common.answer_votes import mirror_vote
from prepza_common.i18n import request_language
from prepza_common.paging import PageParams

from app.auth import UserWithToken
from app.constants.chat import NOT_FOUND, RESTORE_MINUTES
from app.schemas.conversations import (
    ConversationDetailOut,
    ConversationOut,
    MessageOut,
    VoteIn,
)
from app.services.conversations import open_conversation
from app.services.live_blocks import live
from app.storage import actions, conversations, messages

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(
    auth: UserWithToken, page: PageParams, company_id: UUID | None = None
) -> list[ConversationOut]:
    """The user's conversations, the latest first; about one company when it's given."""
    user, _ = auth
    found = await conversations.of_user(user.uid, company_id, page.offset, page.limit)

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
    found = await conversations.latest(user.uid, RESTORE_MINUTES)

    if found is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return ConversationOut.model_validate(found)


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: UUID, request: Request, auth: UserWithToken
) -> ConversationDetailOut:
    """One of the user's conversations with its messages; their blocks are fetched again with
    the user's token, so they show what the user may see now. One about a company they can no
    longer see is deleted, and is a 404."""
    user, token = auth
    language = request_language(request)
    conversation = await open_conversation(conversation_id, user.uid, token, language)
    found = await messages.of_conversation(conversation.id)
    # Cards still waiting for the user's confirmation (in Redis for a while), by their answer.
    cards: dict[str, list] = {}

    for pending in await actions.of_conversation(conversation.id):
        if pending["user_id"] == user.uid and pending.get("message_id"):
            cards.setdefault(pending["message_id"], []).append(pending["card"])

    shown = [
        MessageOut.model_validate(item).model_copy(
            update={
                "blocks": [
                    *await live(item.blocks, token, language),
                    *cards.get(str(item.id), []),
                ]
            }
        )
        for item in found
    ]

    return ConversationDetailOut(
        **ConversationOut.model_validate(conversation).model_dump(), messages=shown
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: UUID, auth: UserWithToken) -> None:
    user, _ = auth

    if await conversations.owned(conversation_id, user.uid) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    await conversations.delete_one(conversation_id)


@router.put("/{conversation_id}/messages/{message_id}/vote", status_code=status.HTTP_204_NO_CONTENT)
async def vote(conversation_id: UUID, message_id: UUID, body: VoteIn, auth: UserWithToken) -> None:
    """The user's thumbs up or down on one of the assistant's answers in their own
    conversation, one an answer: a new vote replaces it, null clears it. Sent on to Langfuse
    as a score on the answer's trace when Langfuse is set up."""
    user, _ = auth
    found, trace_id = await messages.set_vote(conversation_id, user.uid, message_id, body.value)

    if not found:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)

    mirror_vote(trace_id, lambda: messages.vote_of(message_id))
