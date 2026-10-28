import uuid
from datetime import datetime

from prepza_common.config.constants import DEFAULT_LANGUAGE, DELETE_BATCH
from sqlalchemy import String, and_, bindparam, or_, select, text
from sqlalchemy import update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from generation.constants.generation import SWEEP_BATCH
from generation.constants.kinds import GenerationKind
from generation.constants.statuses import FINISHED, Status
from generation.models.generation import Generation
from generation.repositories import outbox


async def create(
    session: AsyncSession,
    owner_uid: str,
    text: str,
    company_id=None,
    language: str = DEFAULT_LANGUAGE,
    generation_id: uuid.UUID | None = None,
    kind: str = GenerationKind.INTERVIEW,
) -> Generation:
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

    return generation


async def create_addition(
    session: AsyncSession,
    owner_uid: str,
    template_id: uuid.UUID,
    language: str,
    question_count: int | None,
) -> Generation:
    """A question addition to a template, queued. Raises IntegrityError while another one for it
    is queued or running (the unique index ix_generations_one_addition_per_template)."""
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
    await session.flush()

    return generation


async def latest_addition(session: AsyncSession, template_id: uuid.UUID) -> Generation | None:
    query = (
        select(Generation)
        .where(
            Generation.kind == GenerationKind.TEMPLATE_QUESTIONS,
            Generation.preparation_id == template_id,
        )
        .order_by(Generation.created_at.desc())
        .limit(1)
    )

    return await session.scalar(query)


async def get(session: AsyncSession, generation_id: uuid.UUID) -> Generation | None:
    return await session.get(Generation, generation_id, populate_existing=True)


async def by_ids(session: AsyncSession, generation_ids: list) -> list[Generation]:
    """The generations of those ids that still exist."""
    if not generation_ids:
        return []

    return list(await session.scalars(select(Generation).where(Generation.id.in_(generation_ids))))


async def update(
    session: AsyncSession,
    generation_id: uuid.UUID,
    event: tuple[str, dict] | None = None,
    **values,
) -> bool:
    """Never touches a finished (done or cancelled) generation, so a job still running can't
    bring it back or move it on. An `event` is saved with the change, for the outbox to publish.
    False when nothing changed."""
    result = await session.execute(
        sql_update(Generation)
        .where(Generation.id == generation_id, Generation.status.not_in(FINISHED))
        .values(**values)
    )

    if event and result.rowcount:
        outbox.add(session, event)

    return result.rowcount == 1


async def claim_run(session: AsyncSession, generation_id: uuid.UUID) -> bool:
    """Atomically moves a queued generation to running; False when it isn't queued (cancelled,
    failed, or claimed by another delivery of its job), so a job never runs twice."""
    result = await session.execute(
        sql_update(Generation)
        .where(Generation.id == generation_id, Generation.status == Status.QUEUED)
        .values(status=Status.RUNNING, error=None)
    )

    return result.rowcount == 1


async def cancel(session: AsyncSession, generation_id: uuid.UUID) -> bool:
    """Atomically cancel a generation that hasn't finished; False if it already has."""
    result = await session.execute(
        sql_update(Generation)
        .where(
            Generation.id == generation_id,
            Generation.status.not_in(FINISHED),
        )
        .values(status=Status.CANCELLED)
    )

    return result.rowcount == 1


def batch_of(condition):
    """The ids of up to SWEEP_BATCH generations matching `condition`, locked for the update that
    uses them; rows another sweep holds are skipped."""
    return (
        select(Generation.id).where(condition).limit(SWEEP_BATCH).with_for_update(skip_locked=True)
    )


async def fail_stuck(
    session: AsyncSession, running_before: datetime, queued_before: datetime, error: str
) -> list[Generation]:
    """Marks up to SWEEP_BATCH generations running untouched since `running_before`, or queued
    since `queued_before`, as failed; returns them. A queued one may only be waiting for the
    queue, so it gets longer. Two sweeps at once take different ones."""
    stuck = or_(
        and_(Generation.status == Status.RUNNING, Generation.updated_at < running_before),
        and_(Generation.status == Status.QUEUED, Generation.updated_at < queued_before),
    )
    failed = await session.scalars(
        sql_update(Generation)
        .where(Generation.id.in_(batch_of(stuck)))
        .values(status=Status.FAILED, error=error)
        .returning(Generation)
    )

    return list(failed)


async def expire_reviews(session: AsyncSession, before: datetime) -> list[Generation]:
    """Cancels up to SWEEP_BATCH generations awaiting review since before `before`; returns
    them."""
    waiting = and_(Generation.status == Status.AWAITING_REVIEW, Generation.updated_at < before)
    expired = await session.scalars(
        sql_update(Generation)
        .where(Generation.id.in_(batch_of(waiting)))
        .values(status=Status.CANCELLED)
        .returning(Generation)
    )

    return list(expired)


async def finished_threads(session: AsyncSession) -> list[str]:
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

    return list(await session.scalars(query))


async def is_cancelled(session: AsyncSession, generation_id: uuid.UUID) -> bool:
    status = await session.scalar(select(Generation.status).where(Generation.id == generation_id))

    return status == Status.CANCELLED


async def claim_review(session: AsyncSession, generation_id: uuid.UUID) -> bool:
    """Atomically move a generation from awaiting review back to the queue."""
    result = await session.execute(
        sql_update(Generation)
        .where(Generation.id == generation_id, Generation.status == Status.AWAITING_REVIEW)
        .values(status=Status.QUEUED)
    )

    return result.rowcount == 1


async def claim_retry(session: AsyncSession, generation_id: uuid.UUID) -> bool:
    """Atomically move a failed generation back to the queue."""
    result = await session.execute(
        sql_update(Generation)
        .where(Generation.id == generation_id, Generation.status == Status.FAILED)
        .values(status=Status.QUEUED, error=None)
    )

    return result.rowcount == 1
