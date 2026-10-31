from datetime import timedelta
from uuid import UUID

from sqlalchemy import func, literal, select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from testee_common.ai.answer_votes import DOWN

from assistant.constants.chat import Role, Source, Status, ToolState
from assistant.models.answers import Answer
from assistant.models.conversations import Conversation, Message, ToolCall, now


async def add_question(
    session: AsyncSession,
    conversation_id: UUID,
    content: str,
    source: Source,
    page: dict | None = None,
) -> Message:
    """The user's message, with the page it was asked on; the conversation isn't idle from now."""
    message = Message(
        conversation_id=conversation_id,
        role=Role.USER,
        source=source,
        content=content,
        page=page,
    )
    session.add(message)
    await _touch(session, conversation_id)

    return message


async def add_earlier(session: AsyncSession, conversation_id: UUID, turns: list) -> None:
    """Messages from before the user signed in, in their order, at the start of a new
    conversation."""
    start = now()

    for index, turn in enumerate(turns):
        session.add(
            Message(
                conversation_id=conversation_id,
                role=turn.role,
                source=Source.TEXT,
                content=turn.content,
                created_at=start + timedelta(microseconds=index),
            )
        )


async def add_answer(
    session: AsyncSession, conversation_id: UUID, answer: Answer, status: Status
) -> UUID:
    """The assistant's answer: its text, its blocks as references (ids, see helpers/blocks.py),
    and which tools it called, how long they took and how they ended; never their arguments'
    values or their results, which are other people's data. Its id."""
    message = Message(
        conversation_id=conversation_id,
        role=Role.ASSISTANT,
        content=answer.content,
        blocks=answer.blocks,
        status=status,
        input_tokens=answer.input_tokens,
        output_tokens=answer.output_tokens,
        trace_id=answer.trace_id,
    )
    session.add(message)
    await session.flush()

    for result in answer.results:
        session.add(
            ToolCall(
                message_id=message.id,
                tool=result.tool,
                arguments=sorted(result.arguments),
                status_code=result.status_code,
                duration_ms=result.duration_ms,
                result=None,
                state=ToolState.DONE if result.succeeded else ToolState.FAILED,
            )
        )

    await _touch(session, conversation_id)

    return message.id


async def _touch(session: AsyncSession, conversation_id: UUID) -> None:
    await session.execute(
        update(Conversation).where(Conversation.id == conversation_id).values(updated_at=now())
    )


async def recent(session: AsyncSession, conversation_id: UUID, limit: int) -> list[Message]:
    """The latest `limit` messages, oldest first."""
    messages = list(
        await session.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc(), Message.id)
            .limit(limit)
        )
    )

    return list(reversed(messages))


async def page_before(
    session: AsyncSession, conversation_id: UUID, before: UUID | None, limit: int
) -> tuple[list[Message], bool]:
    """The `limit` messages before the message `before` (the latest without it), oldest first,
    and whether earlier ones are left."""
    query = select(Message).where(Message.conversation_id == conversation_id)

    if before is not None:
        at = select(Message.created_at).where(Message.id == before).scalar_subquery()
        query = query.where(tuple_(Message.created_at, Message.id) < tuple_(at, literal(before)))

    query = query.order_by(Message.created_at.desc(), Message.id.desc()).limit(limit + 1)

    found = list(await session.scalars(query))

    return list(reversed(found[:limit])), len(found) > limit


async def export(session: AsyncSession, user_id: str) -> list[dict]:
    """The user's conversations with their messages (text, and the blocks' references), oldest
    first."""
    conversations = list(
        await session.scalars(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at, Conversation.id)
        )
    )
    messages = await session.scalars(
        select(Message)
        .where(Message.conversation_id.in_([item.id for item in conversations]))
        .order_by(Message.created_at, Message.id)
    )

    messages = list(messages)
    tools = await session.scalars(
        select(ToolCall)
        .where(ToolCall.message_id.in_([message.id for message in messages]))
        .order_by(ToolCall.created_at, ToolCall.id)
    )
    tools_of: dict[UUID, list[dict]] = {}

    for call in tools:
        tools_of.setdefault(call.message_id, []).append(
            {"tool": call.tool, "arguments": call.arguments, "state": call.state}
        )

    by_conversation: dict[UUID, list[dict]] = {}

    for message in messages:
        by_conversation.setdefault(message.conversation_id, []).append(
            {
                "role": message.role,
                "source": message.source,
                "content": message.content,
                "blocks": message.blocks,
                "page": message.page,
                "status": message.status,
                "vote": message.vote,
                "tools": tools_of.get(message.id, []),
                "at": message.created_at,
            }
        )

    return [
        {
            "company_id": conversation.company_id,
            "title": conversation.title,
            "at": conversation.created_at,
            "messages": by_conversation.get(conversation.id, []),
        }
        for conversation in conversations
    ]


async def count_questions(session: AsyncSession, conversation_id: UUID) -> int:
    """How many messages the user sent in the conversation."""
    return await session.scalar(
        select(func.count())
        .select_from(Message)
        .where(Message.conversation_id == conversation_id, Message.role == Role.USER)
    )


async def set_vote(
    session: AsyncSession, conversation_id: UUID, user_id: str, message_id: UUID, vote: int | None
) -> tuple[bool, str | None]:
    """Sets or clears the vote on an answer in the user's own conversation: whether there was
    one, and its Langfuse trace."""
    owned = select(Conversation.id).where(
        Conversation.id == conversation_id, Conversation.user_id == user_id
    )
    statement = (
        update(Message)
        .where(
            Message.id == message_id,
            Message.role == Role.ASSISTANT,
            Message.conversation_id.in_(owned),
        )
        .values(vote=vote)
        .returning(Message.trace_id)
    )

    found = (await session.execute(statement)).first()

    return (found is not None, found[0] if found else None)


async def vote_of(session: AsyncSession, message_id: UUID) -> int | None:
    return await session.scalar(select(Message.vote).where(Message.id == message_id))


async def voted_down(session: AsyncSession) -> list[tuple[Message, str | None]]:
    """Answers voted down, newest first, each with the user's message it answered (the latest
    before it in its conversation), for the evals' feedback cases
    (evals/scripts/disliked_answers.py)."""
    asked = aliased(Message)
    question = (
        select(asked.content)
        .where(
            asked.conversation_id == Message.conversation_id,
            asked.role == Role.USER,
            asked.created_at < Message.created_at,
        )
        .order_by(asked.created_at.desc())
        .limit(1)
        .scalar_subquery()
    )
    query = (
        select(Message, question)
        .where(Message.role == Role.ASSISTANT, Message.vote == DOWN)
        .order_by(Message.created_at.desc(), Message.id)
    )

    return [tuple(row) for row in await session.execute(query)]
