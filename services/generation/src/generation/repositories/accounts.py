from datetime import datetime

from prepza_common.config.constants import DELETE_BATCH, DELETED_USER
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from generation.constants.statuses import Status
from generation.models.generation import Generation

FINISHED = (Status.DONE, Status.FAILED, Status.CANCELLED)


async def delete_user(session: AsyncSession, user_id: str) -> None:
    """Every generation belongs to a company, so it stays, without the user's id. Safe to
    repeat."""
    await session.execute(
        update(Generation).where(Generation.owner_uid == user_id).values(owner_uid=DELETED_USER)
    )


async def export(session: AsyncSession, user_id: str) -> list[dict]:
    query = (
        select(Generation).where(Generation.owner_uid == user_id).order_by(Generation.created_at)
    )

    return [
        {
            "created_at": row.created_at,
            "status": row.status,
            "pasted_text": row.text,
            "topics": [topic.get("main_topic") for topic in row.topics or []],
        }
        for row in await session.scalars(query)
    ]


async def forget_texts_batch(session: AsyncSession, before: datetime) -> list:
    """Blanks the pasted texts of up to DELETE_BATCH generations finished before `before` (the
    saved tests stay); returns their ids, whose checkpoints still hold the texts. The service
    runs a batch a transaction, so a long backlog never holds one long lock."""
    chosen = (
        select(Generation.id)
        .where(
            Generation.status.in_(FINISHED),
            Generation.updated_at < before,
            Generation.text != "",
        )
        .limit(DELETE_BATCH)
    )

    return list(
        await session.scalars(
            update(Generation)
            .where(Generation.id.in_(chosen))
            .values(text="")
            .returning(Generation.id)
        )
    )
