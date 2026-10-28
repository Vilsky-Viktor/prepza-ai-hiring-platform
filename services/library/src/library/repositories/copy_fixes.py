import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from library.constants.quality import COPY_FIX_BATCH
from library.models.sets import Question
from library.repositories import quality


async def fix_copies(
    session: AsyncSession, question_id: uuid.UUID, old_text: str, old_options: list[dict]
) -> list[uuid.UUID]:
    """Up to COPY_FIX_BATCH copies of a fixed bank question that still hold its old content
    (not one a company changed, nor one fixed on its own) get its current content, each kept as
    a fixed revision; their ids. Copies another run holds are skipped, and a fixed copy no
    longer matches, so running it again fixes nothing twice."""
    original = await session.get(Question, question_id)

    if original is None:
        return []

    copies = list(
        await session.scalars(
            select(Question.id)
            .where(
                Question.source_question_id == question_id,
                Question.text == old_text,
                Question.options == old_options,
            )
            .limit(COPY_FIX_BATCH)
            .with_for_update(skip_locked=True)
        )
    )

    for copy_id in copies:
        await quality.archive(session, copy_id, fixed=True)

    if copies:
        await session.execute(
            update(Question)
            .where(Question.id.in_(copies))
            .values(text=original.text, options=original.options)
        )

    return copies
