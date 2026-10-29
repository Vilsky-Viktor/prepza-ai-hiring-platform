import uuid

from prepza_common.ai.answer_votes import DOWN
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from assistant.models.help_votes import HelpVote


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


async def voted_down(session: AsyncSession) -> list[HelpVote]:
    """The help chat's answers voted down, newest first, for the evals' feedback cases
    (evals/scripts/disliked_answers.py): only their ids and traces, as the chat keeps no text."""
    query = select(HelpVote).where(HelpVote.vote == DOWN).order_by(HelpVote.updated_at.desc())

    return list(await session.scalars(query))
