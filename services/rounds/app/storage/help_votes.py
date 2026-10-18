import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert

from app.models.help_votes import HelpVote
from app.storage.db import Session


async def save(answer_id: uuid.UUID, trace_id: str | None, vote: int | None) -> None:
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

    async with Session() as session:
        await session.execute(statement)
        await session.commit()


async def vote_of(answer_id: uuid.UUID) -> int | None:
    async with Session() as session:
        return await session.scalar(select(HelpVote.vote).where(HelpVote.answer_id == answer_id))
