import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from prepza_common import outbox
from sqlalchemy import delete, func, select, update

from app.constants.events import CANDIDATE_INTERVIEW_DELETED, INTERVIEW_DELETED
from app.constants.invites import InviteStatus
from app.core.exceptions import OverLimit
from app.helpers.search import escape_like
from app.helpers.sync import changed_since
from app.models.interviews import Interview
from app.models.invites import CandidateInvite
from app.models.outbox import OutboxEvent
from app.schemas.interviews import InterviewSettings
from app.storage import guests
from app.storage.db import Session


def company_of(interview_id):
    """The interview's company, read by the statement that saves a row of it."""
    return select(Interview.company_id).where(Interview.id == interview_id).scalar_subquery()


async def create(
    company_id, generation_id, language: str, seconds: int, most: int | None = None
) -> Interview:
    """A generated test, waiting for its questions: `seconds` a question until its level is
    known (interview_generations.set_generated). OverLimit when the company already has `most`
    interviews without candidates, counted under a lock with the insert, so two made at once
    can't both pass."""
    interview = Interview(
        company_id=company_id,
        generation_id=generation_id,
        set_id=None,
        language=language,
        question_seconds=seconds,
    )

    async with Session() as session:
        lock = func.pg_advisory_xact_lock(func.hashtext(f"interviews:{company_id}"))
        await session.execute(select(lock))

        if most is not None:
            count = await session.scalar(without_candidates_query(company_id))

            if count >= most:
                raise OverLimit(count)

        session.add(interview)
        await session.commit()

    return interview


async def create_from_template(
    company_id, set_id, title: str, language: str, seconds: int
) -> Interview:
    """A test whose questions were copied from a template: ready at once, with no generation,
    `seconds` a question (its level's)."""
    interview = Interview(
        company_id=company_id,
        generation_id=None,
        set_id=set_id,
        title=title,
        language=language,
        question_seconds=seconds,
        ready_at=datetime.now(UTC),
    )

    async with Session() as session:
        session.add(interview)
        await session.commit()

    return interview


async def get_by_link(token: str) -> Interview | None:
    query = select(Interview).where(Interview.link_token == token)

    async with Session() as session:
        return await session.scalar(query)


async def set_link(interview_id, token: str | None) -> None:
    async with Session() as session:
        await session.execute(
            update(Interview).where(Interview.id == interview_id).values(link_token=token)
        )
        await session.commit()


async def get(interview_id) -> Interview | None:
    async with Session() as session:
        return await session.get(Interview, interview_id)


async def counts(company_ids: list) -> dict:
    if not company_ids:
        return {}

    query = (
        select(Interview.company_id, func.count())
        .where(Interview.company_id.in_(company_ids))
        .group_by(Interview.company_id)
    )

    async with Session() as session:
        rows = await session.execute(query)

    return {company_id: count for company_id, count in rows}


def without_candidates_query(company_id):
    invited = select(CandidateInvite.id).where(CandidateInvite.interview_id == Interview.id)

    return (
        select(func.count())
        .select_from(Interview)
        .where(
            Interview.company_id == company_id,
            Interview.generation_id.is_not(None),
            ~invited.exists(),
        )
    )


async def without_candidates(company_id) -> int:
    """The company's generated interviews no candidate is invited to (yet, or any more); copies
    of templates cost nothing and aren't counted."""
    async with Session() as session:
        return await session.scalar(without_candidates_query(company_id)) or 0


async def list_for_company(
    company_id,
    offset: int = 0,
    limit: int | None = None,
    since: datetime | None = None,
    after: uuid.UUID | None = None,
    q: str = "",
) -> list[Interview]:
    """Newest first; without a limit, all of them (deleting a company goes through each). With
    `since`, those changed since, oldest change first (changed_since); with `q`, those whose
    title contains it as typed, in any case."""
    filters = [Interview.company_id == company_id]

    if q:
        filters.append(Interview.title.ilike(f"%{escape_like(q.lower())}%", escape="\\"))
    order = [Interview.created_at.desc(), Interview.id]

    if since is not None:
        synced, order = changed_since(Interview, since, after)
        filters += synced

    query = select(Interview).where(*filters).order_by(*order).offset(offset).limit(limit)

    async with Session() as session:
        return list(await session.scalars(query))


async def update_settings(interview_id, settings: InterviewSettings) -> None:
    """Saves the settings that were sent; marking the test hired also turns its shareable link
    off, so a job ad left online stops bringing in candidates."""
    values = settings.model_dump(exclude_none=True)

    if not values:
        return

    if settings.hired:
        values["link_token"] = None

    async with Session() as session:
        await session.execute(
            update(Interview).where(Interview.id == interview_id).values(**values)
        )
        await session.commit()


async def set_topic_limit(
    interview_id, topic_id: uuid.UUID, limit: int, allowed: Callable[[dict[str, int]], bool]
) -> bool:
    """Sets the topic's number of questions, when `allowed` takes the new numbers; False, with
    nothing changed, when it doesn't. Locked, so two changes at once both see the other."""
    async with Session() as session:
        interview = await session.scalar(
            select(Interview).where(Interview.id == interview_id).with_for_update()
        )
        limits = {**interview.topic_limits, str(topic_id): limit}

        if not allowed(limits):
            return False

        interview.topic_limits = limits
        await session.commit()

    return True


async def remove(interview_id) -> list[tuple]:
    """Deletes the interview, with the interview.deleted event when one is removed, and returns
    (interview id, email, status, hold key) of its invites not finished, deleted with it."""
    async with Session() as session:
        # Locked first: an invite being saved now is saved before and returned, or waits and
        # then fails, as its interview is gone.
        await session.scalar(
            select(Interview.id).where(Interview.id == interview_id).with_for_update()
        )
        # Finished invites go too, with the interview (cascade).
        await guests.announce_deleted(session, CandidateInvite.interview_id == interview_id)
        removed = await session.execute(
            delete(CandidateInvite)
            .where(
                CandidateInvite.interview_id == interview_id,
                CandidateInvite.status != InviteStatus.FINISHED,
            )
            .returning(
                CandidateInvite.interview_id,
                CandidateInvite.email,
                CandidateInvite.status,
                CandidateInvite.hold_key,
            )
        )
        removed = [tuple(row) for row in removed]
        company_id = await session.scalar(
            delete(Interview).where(Interview.id == interview_id).returning(Interview.company_id)
        )

        if company_id is not None:
            add_deleted(session, interview_id, company_id)

        await session.commit()

    return removed


def add_deleted(session, interview_id, company_id) -> None:
    """ats removes the deleted interview's job links and candidates; notifications and the api
    forget its candidates."""
    data = {"interview_id": str(interview_id), "company_id": str(company_id)}
    outbox.add(session, OutboxEvent, INTERVIEW_DELETED, data)
    outbox.add(session, OutboxEvent, CANDIDATE_INTERVIEW_DELETED, data)


async def set_title(interview_id, title: str) -> None:
    async with Session() as session:
        await session.execute(
            update(Interview).where(Interview.id == interview_id).values(title=title)
        )
        await session.commit()


async def by_ids(interview_ids: list) -> list[Interview]:
    """The interviews of those ids that still exist."""
    if not interview_ids:
        return []

    async with Session() as session:
        return list(await session.scalars(select(Interview).where(Interview.id.in_(interview_ids))))
