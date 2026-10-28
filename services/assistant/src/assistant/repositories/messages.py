from datetime import timedelta
from uuid import UUID

from sqlalchemy import func, literal, select, tuple_, update

from assistant.constants.chat import Role, Source, Status, ToolState
from assistant.core.db import Session
from assistant.models.answers import Answer
from assistant.models.conversations import Conversation, Message, ToolCall, now


async def add_question(
    conversation_id: UUID, content: str, source: Source, page: dict | None = None
) -> Message:
    """The user's message, with the page it was asked on; the conversation isn't idle from now."""
    async with Session() as session:
        message = Message(
            conversation_id=conversation_id,
            role=Role.USER,
            source=source,
            content=content,
            page=page,
        )
        session.add(message)
        await _touch(session, conversation_id)
        await session.commit()

        return message


async def add_earlier(conversation_id: UUID, turns: list) -> None:
    """Messages from before the user signed in, in their order, at the start of a new
    conversation."""
    async with Session() as session:
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

        await session.commit()


async def add_answer(conversation_id: UUID, answer: Answer, status: Status) -> UUID:
    """The assistant's answer: its text, its blocks as references (ids, see helpers/blocks.py),
    and which tools it called, how long they took and how they ended; never their arguments'
    values or their results, which are other people's data. Its id."""
    async with Session() as session:
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
        await session.commit()

        return message.id


async def _touch(session, conversation_id: UUID) -> None:
    await session.execute(
        update(Conversation).where(Conversation.id == conversation_id).values(updated_at=now())
    )


async def recent(conversation_id: UUID, limit: int) -> list[Message]:
    """The latest `limit` messages, oldest first."""
    async with Session() as session:
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
    conversation_id: UUID, before: UUID | None, limit: int
) -> tuple[list[Message], bool]:
    """The `limit` messages before the message `before` (the latest without it), oldest first,
    and whether earlier ones are left."""
    query = select(Message).where(Message.conversation_id == conversation_id)

    if before is not None:
        at = select(Message.created_at).where(Message.id == before).scalar_subquery()
        query = query.where(tuple_(Message.created_at, Message.id) < tuple_(at, literal(before)))

    query = query.order_by(Message.created_at.desc(), Message.id.desc()).limit(limit + 1)

    async with Session() as session:
        found = list(await session.scalars(query))

    return list(reversed(found[:limit])), len(found) > limit


async def export(user_id: str) -> list[dict]:
    """The user's conversations with their messages (text, and the blocks' references), oldest
    first."""
    async with Session() as session:
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


async def count_questions(conversation_id: UUID) -> int:
    """How many messages the user sent in the conversation."""
    async with Session() as session:
        return await session.scalar(
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == conversation_id, Message.role == Role.USER)
        )


async def set_vote(
    conversation_id: UUID, user_id: str, message_id: UUID, vote: int | None
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

    async with Session() as session:
        found = (await session.execute(statement)).first()
        await session.commit()

    return (found is not None, found[0] if found else None)


async def vote_of(message_id: UUID) -> int | None:
    async with Session() as session:
        return await session.scalar(select(Message.vote).where(Message.id == message_id))
