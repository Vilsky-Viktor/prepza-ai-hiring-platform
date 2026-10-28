import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from rounds.models.help_votes import HelpVote


async def save(
    session: AsyncSession, answer_id: uuid.UUID, trace_id: str | None, vote: int | None
) -> None:
    """Sets the answer's vote, or clears it (None)."""
    if vote is None:
        statement = delete(HelpVote).where(HelpVote.answer_id == answer_id)
    else:
        statement = (
            insert(HelpVote)
            .values(answer_id=answer_id, trace_id=trace_id, vote=vote)
            .on_conflict_do_update(
                index_elements=[HelpVote.answer_id],
                set_={"vote": vote, "updated_at": func.now()},
            )
        )

    await session.execute(statement)


async def vote_of(session: AsyncSession, answer_id: uuid.UUID) -> int | None:
    return await session.scalar(select(HelpVote.vote).where(HelpVote.answer_id == answer_id))
