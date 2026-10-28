import uuid
from datetime import datetime

from prepza_common.config.constants import DEFAULT_LANGUAGE, DELETE_BATCH
from prepza_common.events import outbox
from sqlalchemy import String, and_, bindparam, or_, select, text
from sqlalchemy import update as sql_update
from sqlalchemy.exc import IntegrityError

from generation.constants.events import GENERATION_CANCELLED
from generation.constants.generation import SWEEP_BATCH
from generation.constants.kinds import GenerationKind
from generation.constants.statuses import FINISHED, Status
from generation.core.db import Session
from generation.helpers.events import failed_event
from generation.models.generation import Generation
from generation.models.outbox import OutboxEvent


async def create(
    owner_uid: str,
    text: str,
    company_id=None,
    language: str = DEFAULT_LANGUAGE,
    generation_id: uuid.UUID | None = None,
    kind: str = GenerationKind.INTERVIEW,
) -> Generation:
    async with Session() as session:
        generation = Generation(
            id=generation_id or uuid.uuid4(),
            owner_uid=owner_uid,
            kind=kind,
            company_id=company_id,
            text=text,
            language=language,
            status=Status.QUEUED,
        )
        session.add(generation)
        await session.commit()

        return generation


async def create_addition(
    owner_uid: str, template_id: uuid.UUID, language: str, question_count: int | None
) -> Generation | None:
    """A question addition to a template, queued; None while another one for it is queued or
    running (the unique index ix_generations_one_addition_per_template)."""
    try:
        async with Session() as session:
            generation = Generation(
                owner_uid=owner_uid,
                kind=GenerationKind.TEMPLATE_QUESTIONS,
                text="",
                language=language,
                status=Status.QUEUED,
                preparation_id=template_id,
                question_count=question_count,
            )
            session.add(generation)
            await session.commit()

            return generation
    except IntegrityError:
        return None


async def latest_addition(template_id: uuid.UUID) -> Generation | None:
    query = (
        select(Generation)
        .where(
            Generation.kind == GenerationKind.TEMPLATE_QUESTIONS,
            Generation.preparation_id == template_id,
        )
        .order_by(Generation.created_at.desc())
        .limit(1)
    )

    async with Session() as session:
        return await session.scalar(query)


async def get(generation_id: uuid.UUID) -> Generation | None:
    async with Session() as session:
        return await session.get(Generation, generation_id)


async def by_ids(generation_ids: list) -> list[Generation]:
    """The generations of those ids that still exist."""
    if not generation_ids:
        return []

    async with Session() as session:
        return list(
            await session.scalars(select(Generation).where(Generation.id.in_(generation_ids)))
        )


async def update(generation_id: uuid.UUID, event: tuple[str, dict] | None = None, **values) -> bool:
    """Never touches a finished (done or cancelled) generation, so a job still running can't
    bring it back or move it on. An `event` is saved with the change, for the outbox to publish.
    False when nothing changed."""
    async with Session() as session:
        result = await session.execute(
            sql_update(Generation)
            .where(Generation.id == generation_id, Generation.status.not_in(FINISHED))
            .values(**values)
        )

        if event and result.rowcount:
            outbox.add(session, OutboxEvent, *event)

        await session.commit()

        return result.rowcount == 1


async def claim_run(generation_id: uuid.UUID) -> bool:
    """Atomically moves a queued generation to running; False when it isn't queued (cancelled,
    failed, or claimed by another delivery of its job), so a job never runs twice."""
    async with Session() as session:
        result = await session.execute(
            sql_update(Generation)
            .where(Generation.id == generation_id, Generation.status == Status.QUEUED)
            .values(status=Status.RUNNING, error=None)
        )
        await session.commit()

        return result.rowcount == 1


async def cancel(generation_id: uuid.UUID) -> bool:
    """Atomically cancel a generation that hasn't finished; False if it already has."""
    async with Session() as session:
        result = await session.execute(
            sql_update(Generation)
            .where(
                Generation.id == generation_id,
                Generation.status.not_in(FINISHED),
            )
            .values(status=Status.CANCELLED)
        )
        await session.commit()

        return result.rowcount == 1


def batch_of(condition):
    """The ids of up to SWEEP_BATCH generations matching `condition`, locked for the update that
    uses them; rows another sweep holds are skipped."""
    return (
        select(Generation.id).where(condition).limit(SWEEP_BATCH).with_for_update(skip_locked=True)
    )


async def fail_stuck(running_before: datetime, queued_before: datetime, error: str) -> list:
    """Marks up to SWEEP_BATCH generations running untouched since `running_before`, or queued
    since `queued_before`, as failed, with the event that tells companies of each interview's
    failure; returns them. A queued one may only be waiting for the queue, so it gets longer.
    Two sweeps at once take different ones."""
    stuck = or_(
        and_(Generation.status == Status.RUNNING, Generation.updated_at < running_before),
        and_(Generation.status == Status.QUEUED, Generation.updated_at < queued_before),
    )

    async with Session() as session:
        failed = await session.scalars(
            sql_update(Generation)
            .where(Generation.id.in_(batch_of(stuck)))
            .values(status=Status.FAILED, error=error)
            .returning(Generation)
        )
        failed = list(failed)

        for generation in failed:
            event = failed_event(generation)

            if event:
                outbox.add(session, OutboxEvent, *event)

        await session.commit()

        return failed


async def expire_reviews(before: datetime) -> list[Generation]:
    """Cancels up to SWEEP_BATCH generations awaiting review since before `before`; returns
    them."""
    waiting = and_(Generation.status == Status.AWAITING_REVIEW, Generation.updated_at < before)

    async with Session() as session:
        expired = await session.scalars(
            sql_update(Generation)
            .where(Generation.id.in_(batch_of(waiting)))
            .values(status=Status.CANCELLED)
            .returning(Generation)
        )
        expired = list(expired)

        # Companies removes the interview of an expired review.
        for generation in expired:
            if generation.kind != GenerationKind.INTERVIEW:
                continue

            outbox.add(
                session,
                OutboxEvent,
                GENERATION_CANCELLED,
                {"generation_id": str(generation.id)},
            )

        await session.commit()

        return expired


async def finished_threads() -> list[str]:
    """Up to DELETE_BATCH checkpoint threads of done or cancelled generations, which nothing
    resumes; the next run takes the rest."""
    query = text(
        "SELECT DISTINCT c.thread_id FROM checkpoints c "
        "JOIN generations g ON c.thread_id = g.id::text "
        "WHERE g.status IN :statuses LIMIT :most"
    ).bindparams(
        bindparam("statuses", list(FINISHED), expanding=True, type_=String()),
        most=DELETE_BATCH,
    )

    async with Session() as session:
        return list(await session.scalars(query))


async def is_cancelled(generation_id: uuid.UUID) -> bool:
    async with Session() as session:
        status = await session.scalar(
            select(Generation.status).where(Generation.id == generation_id)
        )

    return status == Status.CANCELLED


async def claim_review(generation_id: uuid.UUID) -> bool:
    """Atomically move a generation from awaiting review back to the queue."""
    async with Session() as session:
        result = await session.execute(
            sql_update(Generation)
            .where(Generation.id == generation_id, Generation.status == Status.AWAITING_REVIEW)
            .values(status=Status.QUEUED)
        )
        await session.commit()

        return result.rowcount == 1


async def claim_retry(generation_id: uuid.UUID) -> bool:
    """Atomically move a failed generation back to the queue."""
    async with Session() as session:
        result = await session.execute(
            sql_update(Generation)
            .where(Generation.id == generation_id, Generation.status == Status.FAILED)
            .values(status=Status.QUEUED, error=None)
        )
        await session.commit()

        return result.rowcount == 1
