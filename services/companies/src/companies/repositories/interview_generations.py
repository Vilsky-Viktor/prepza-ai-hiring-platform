import uuid

from prepza_common.events import outbox, processed_events
from prepza_common.events.notifications import NOTIFICATION_REQUESTED
from sqlalchemy import case, delete, func, select, update

from companies.constants.events import INTERVIEW_READY
from companies.core.db import Session
from companies.models.events import ProcessedEvent
from companies.models.interviews import Interview
from companies.models.outbox import OutboxEvent
from companies.repositories.interviews import add_deleted


async def set_set_id(interview_id, set_id: uuid.UUID) -> None:
    async with Session() as session:
        await session.execute(
            update(Interview)
            .where(Interview.id == interview_id)
            .values(set_id=set_id, generation_failed=False)
        )
        await session.commit()


async def get_for_generation(generation_id: uuid.UUID) -> Interview | None:
    query = select(Interview).where(Interview.generation_id == generation_id)

    async with Session() as session:
        return await session.scalar(query)


async def set_generated(
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

    async with Session() as session:
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
            .returning(Interview.id, Interview.company_id)
        )
        found = row.one_or_none()

        if new:
            outbox.add(session, OutboxEvent, NOTIFICATION_REQUESTED, notice)

        if new and found is not None:
            outbox.add(
                session,
                OutboxEvent,
                INTERVIEW_READY,
                {"interview_id": str(found.id), "company_id": str(found.company_id)},
            )

        await session.commit()


async def mark_failed(generation_id: uuid.UUID, event_id: str) -> None:
    """Marks the interview of a failed generation, once per event: a late redelivery doesn't
    mark it again after a retry. One with its questions already isn't touched."""
    async with Session() as session:
        if await processed_events.claim(session, ProcessedEvent, event_id):
            await session.execute(
                update(Interview)
                .where(Interview.generation_id == generation_id, Interview.set_id.is_(None))
                .values(generation_failed=True)
            )

        await session.commit()


async def set_generation_failed(interview_id, failed: bool) -> None:
    async with Session() as session:
        await session.execute(
            update(Interview).where(Interview.id == interview_id).values(generation_failed=failed)
        )
        await session.commit()


async def remove_for_generation(generation_id: uuid.UUID, notice: dict) -> None:
    """Removes the interview of a generation that was cancelled before producing questions;
    the company's notification and the interview.deleted event are saved only when one is
    removed."""
    async with Session() as session:
        removed = (
            await session.execute(
                delete(Interview)
                .where(Interview.generation_id == generation_id, Interview.set_id.is_(None))
                .returning(Interview.id, Interview.company_id)
            )
        ).first()

        if removed is not None:
            outbox.add(session, OutboxEvent, NOTIFICATION_REQUESTED, notice)
            add_deleted(session, *removed)

        await session.commit()
