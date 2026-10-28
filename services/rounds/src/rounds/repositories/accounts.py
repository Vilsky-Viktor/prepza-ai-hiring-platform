from prepza_common.db.db import delete_in_batches
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from rounds.constants.rounds import SESSION_DELETE_BATCH
from rounds.models.sessions import Session as RoundSession


async def delete_user(sessions, user_id: str) -> None:
    """Everything rounds holds about a user: interview and practice sessions with their answers
    and signals, SESSION_DELETE_BATCH sessions at a time, each batch its own transaction (from
    `sessions`). Safe to repeat."""
    await delete_in_batches(
        sessions, RoundSession, RoundSession.user_id == user_id, batch=SESSION_DELETE_BATCH
    )


async def user_ids(session: AsyncSession, practice: bool, after: str, limit: int) -> list[str]:
    """The people who took a company's interview (never a member's own try, a preview), or with
    `practice` a free practice round, once each, in order: up to `limit` after `after`."""
    query = select(RoundSession.user_id).where(
        RoundSession.user_id > after, RoundSession.practice.is_(practice)
    )

    if not practice:
        query = query.where(RoundSession.preview.is_(False))

    rows = await session.scalars(query.distinct().order_by(RoundSession.user_id).limit(limit))

    return list(rows)


async def of_user(session: AsyncSession, user_id: str) -> list[RoundSession]:
    """The user's sessions, with their answers and signals."""
    found = await session.scalars(
        select(RoundSession)
        .where(RoundSession.user_id == user_id)
        .options(selectinload(RoundSession.answers), selectinload(RoundSession.signals))
    )

    return list(found)
