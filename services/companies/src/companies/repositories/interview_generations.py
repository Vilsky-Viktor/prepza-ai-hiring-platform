import uuid

from prepza_common.events import processed_events
from sqlalchemy import case, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from companies.constants.events import INTERVIEW_READY
from companies.models.events import ProcessedEvent
from companies.models.interviews import Interview
from companies.repositories import outbox
from companies.repositories.interviews import add_deleted


async def set_set_id(session: AsyncSession, interview_id, set_id: uuid.UUID) -> None:
    await session.execute(
        update(Interview)
        .where(Interview.id == interview_id)
        .values(set_id=set_id, generation_failed=False)
    )


async def get_for_generation(session: AsyncSession, generation_id: uuid.UUID) -> Interview | None:
    query = select(Interview).where(Interview.generation_id == generation_id)

    return await session.scalar(query)


async def set_generated(
    session: AsyncSession,
    generation_id: uuid.UUID,
    set_id: uuid.UUID,
    title: str,
    seconds: int | None,
    notice: dict,
    event_id: str,
) -> None:
    """Stores the set and title a finished generation produced for its interview, and the
    company's notification and the interview.ready event (ats invites the candidates waiting
    for it) with them, once per event. The first time it's ready, the interview takes `seconds`
    a question (its level's; None keeps its own); after that, they're the company's."""
    kept = Interview.question_seconds
    question_seconds = (
        case((Interview.ready_at.is_(None), seconds), else_=kept) if seconds else kept
    )

    new = await processed_events.claim(session, ProcessedEvent, event_id)
    row = await session.execute(
        update(Interview)
        .where(Interview.generation_id == generation_id)
        .values(
            set_id=set_id,
            title=title,
            question_seconds=question_seconds,
            generation_failed=False,
            ready_at=func.coalesce(Interview.ready_at, func.now()),
        )
        .returning(Interview.id, Interview.company_id, Interview.set_id, Interview.generation_id)
    )
    found = row.one_or_none()

    if new:
        outbox.notify(session, notice)

    if new and found is not None:
        outbox.add(
            session,
            INTERVIEW_READY,
            {"interview_id": str(found.id), "company_id": str(found.company_id)},
        )


async def mark_failed(session: AsyncSession, generation_id: uuid.UUID, event_id: str) -> None:
    """Marks the interview of a failed generation, once per event: a late redelivery doesn't
    mark it again after a retry. One with its questions already isn't touched."""
    if await processed_events.claim(session, ProcessedEvent, event_id):
        await session.execute(
            update(Interview)
            .where(Interview.generation_id == generation_id, Interview.set_id.is_(None))
            .values(generation_failed=True)
        )


async def set_generation_failed(session: AsyncSession, interview_id, failed: bool) -> None:
    await session.execute(
        update(Interview).where(Interview.id == interview_id).values(generation_failed=failed)
    )


async def remove_for_generation(
    session: AsyncSession, generation_id: uuid.UUID, notice: dict
) -> None:
    """Removes the interview of a generation that was cancelled before producing questions;
    the company's notification and the interview.deleted event are saved only when one is
    removed."""
    removed = (
        await session.execute(
            delete(Interview)
            .where(Interview.generation_id == generation_id, Interview.set_id.is_(None))
            .returning(
                Interview.id, Interview.company_id, Interview.set_id, Interview.generation_id
            )
        )
    ).first()

    if removed is not None:
        outbox.notify(session, notice)
        add_deleted(session, *removed)
