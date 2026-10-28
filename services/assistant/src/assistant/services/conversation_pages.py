from uuid import UUID

from assistant.constants.chat import MESSAGES_SHOWN
from assistant.core.db import Session
from assistant.repositories import actions, messages
from assistant.schemas.conversations import MessageOut, MessagesOut
from assistant.services.live_blocks import live


async def messages_page(
    conversation_id: UUID, user_id: str, token: str, language: str, before: UUID | None
) -> MessagesOut:
    """MESSAGES_SHOWN of the conversation's messages before `before` (the latest without it),
    oldest first; their blocks are fetched again with the user's token, so they show what the
    user may see now, with the cards still waiting for the user's confirmation."""
    async with Session() as session:
        found, earlier = await messages.page_before(
            session, conversation_id, before, MESSAGES_SHOWN
        )

    # Cards still waiting for the user's confirmation (in Redis for a while), by their answer.
    cards: dict[str, list] = {}

    for pending in await actions.of_conversation(conversation_id):
        if pending["user_id"] == user_id and pending.get("message_id"):
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

    return MessagesOut(messages=shown, earlier=earlier)
