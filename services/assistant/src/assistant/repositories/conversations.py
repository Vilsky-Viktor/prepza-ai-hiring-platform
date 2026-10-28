from datetime import UTC, datetime, timedelta
from uuid import UUID

from prepza_common.db.db import delete_in_batches
from sqlalchemy import Text, cast, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from assistant.models.conversations import Conversation, Message, ToolCall


async def create(
    session: AsyncSession, user_id: str, company_id: UUID | None, title: str
) -> Conversation:
    conversation = Conversation(user_id=user_id, company_id=company_id, title=title)
    session.add(conversation)
    await session.flush()

    return conversation


async def owned(session: AsyncSession, conversation_id: UUID, user_id: str) -> Conversation | None:
    """The user's own conversation; None when it's gone or someone else's."""
    return await session.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )
    )


async def of_user(
    session: AsyncSession, user_id: str, company_id: UUID | None, offset: int, limit: int
) -> list[Conversation]:
    """The user's conversations, the latest first; about one company when it's given."""
    query = select(Conversation).where(Conversation.user_id == user_id)

    if company_id is not None:
        query = query.where(Conversation.company_id == company_id)

    query = query.order_by(Conversation.updated_at.desc(), Conversation.id)

    return list(await session.scalars(query.offset(offset).limit(limit)))


async def delete_one(session: AsyncSession, conversation_id: UUID) -> None:
    """With its messages and their tool calls (the foreign keys cascade)."""
    await session.execute(delete(Conversation).where(Conversation.id == conversation_id))


async def delete_idle(session: AsyncSession, before: datetime, limit: int) -> int:
    """Up to `limit` conversations nobody added to since `before`; how many went."""
    idle = (
        select(Conversation.id).where(Conversation.updated_at < before).limit(limit)
    ).scalar_subquery()

    result = await session.execute(delete(Conversation).where(Conversation.id.in_(idle)))

    return result.rowcount


async def delete_company(sessions: async_sessionmaker, company_id: UUID) -> int:
    """Every conversation about the company, with its messages, a batch at a time (each its
    own transaction); how many went (none when run again)."""
    return await delete_in_batches(sessions, Conversation, Conversation.company_id == company_id)


def mentions(text, needle: str):
    return func.strpos(func.lower(text), needle.lower()) > 0


async def delete_mentioning(
    sessions: async_sessionmaker, company_id: UUID, needles: list[str]
) -> int:
    """The company's conversations whose messages or tools' results mention any of `needles`
    (an erased candidate's email or invite, a deleted interview): they go whole, as what's left
    of one would still read as about that person. A batch at a time; how many went (none when
    run again)."""
    needles = [needle for needle in needles if needle]

    if not needles:
        return 0

    # Only the company's own messages are read, never every tenant's.
    of_company = Message.conversation_id.in_(
        select(Conversation.id).where(Conversation.company_id == company_id)
    )
    said = select(Message.conversation_id).where(
        of_company,
        or_(
            *(mentions(Message.content, needle) for needle in needles),
            *(mentions(cast(Message.blocks, Text), needle) for needle in needles),
        ),
    )
    read = (
        select(Message.conversation_id)
        .join(ToolCall, ToolCall.message_id == Message.id)
        .where(
            of_company, or_(*(mentions(cast(ToolCall.result, Text), needle) for needle in needles))
        )
    )

    return await delete_in_batches(
        sessions,
        Conversation,
        Conversation.company_id == company_id,
        or_(Conversation.id.in_(said), Conversation.id.in_(read)),
    )


async def trace_ids_of_user(session: AsyncSession, user_id: str) -> list[str]:
    """The Langfuse traces of the user's conversations' answers."""
    query = (
        select(Message.trace_id)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(Conversation.user_id == user_id, Message.trace_id.is_not(None))
    )

    return list(await session.scalars(query))


async def delete_user(session: AsyncSession, user_id: str) -> None:
    await session.execute(delete(Conversation).where(Conversation.user_id == user_id))


async def set_title(session: AsyncSession, conversation_id: UUID, title: str) -> None:
    await session.execute(
        update(Conversation).where(Conversation.id == conversation_id).values(title=title)
    )


async def latest(session: AsyncSession, user_id: str, minutes: int) -> Conversation | None:
    """The user's conversation with the latest message, if that's at most `minutes` old."""
    since = datetime.now(UTC) - timedelta(minutes=minutes)

    return await session.scalar(
        select(Conversation)
        .where(Conversation.user_id == user_id, Conversation.updated_at >= since)
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    )
