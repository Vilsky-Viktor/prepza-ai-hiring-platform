"""A user's data in the assistant, against the real database: the export names the tools each
answer used (never their data), and deleting the account also deletes when its AI app
connections last asked for updates, leaving another user's untouched."""

import uuid
from datetime import UTC, datetime

from assistant.constants.chat import Role, Source
from assistant.core.db import Session
from assistant.models.conversations import Message, ToolCall
from assistant.repositories import conversations, messages, oauth, update_checks
from assistant.services import accounts
from tests.integration.repositories.test_connected_apps import connect
from tests.integration.transactions import transaction


async def answered_with_a_tool(user_id: str) -> None:
    async with Session.begin() as session:
        conversation = await conversations.create(session, user_id, None, "Candidates")
        await messages.add_question(session, conversation.id, "Who finished?", Source.TEXT)
        answer = Message(conversation_id=conversation.id, role=Role.ASSISTANT, content="Ann.")
        session.add(answer)
        await session.flush()
        session.add(
            ToolCall(
                message_id=answer.id,
                tool="list_candidates",
                arguments=["interview_id"],
                status_code=200,
                duration_ms=40,
            )
        )


async def checked_updates(user_id: str) -> list[str]:
    """Each of the user's connections asks for updates once; their ids."""
    async with Session() as session:
        grants = await oauth.of_user(session, user_id)

    ids = [str(grant.id) for grant in grants]

    for connection_id in ids:
        await transaction(update_checks.save, connection_id, datetime.now(UTC))

    return ids


def test_the_export_names_the_tools_and_deletion_takes_the_update_checks(run):
    user, other = f"data-{uuid.uuid4().hex[:8]}", f"data-{uuid.uuid4().hex[:8]}"

    async def scenario():
        await answered_with_a_tool(user)
        await connect(user, "Claude")
        await connect(other, "Claude")
        [mine], [theirs] = await checked_updates(user), await checked_updates(other)
        exported = await accounts.export_user(user)

        # Accounts' event, delivered twice: the second finds nothing left.
        for _ in range(2):
            await accounts.delete_user(user)

        left = (
            await transaction(update_checks.last, mine),
            await transaction(update_checks.last, theirs),
        )
        await accounts.delete_user(other)

        return exported, left

    exported, (mine, theirs) = run(scenario())

    [conversation] = exported["assistant_conversations"]
    question, answer = conversation["messages"]
    assert question["tools"] == []
    assert answer["tools"] == [
        {"tool": "list_candidates", "arguments": ["interview_id"], "state": "done"}
    ]
    assert (mine, theirs is not None) == (None, True)
