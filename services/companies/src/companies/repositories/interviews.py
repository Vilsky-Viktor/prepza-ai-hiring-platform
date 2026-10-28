import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from companies.constants.events import CANDIDATE_INTERVIEW_DELETED, INTERVIEW_DELETED
from companies.constants.invites import InviteStatus
from companies.core.exceptions import OverLimit
from companies.helpers.search import escape_like
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite
from companies.repositories import guests, outbox
from companies.repositories.sync import changed_since
from companies.schemas.interviews import InterviewSettings


def company_of(interview_id):
    """The interview's company, read by the statement that saves a row of it."""
    return select(Interview.company_id).where(Interview.id == interview_id).scalar_subquery()


async def create(
    session: AsyncSession,
    company_id,
    generation_id,
    language: str,
    seconds: int,
    most: int | None = None,
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

    lock = func.pg_advisory_xact_lock(func.hashtext(f"interviews:{company_id}"))
    await session.execute(select(lock))

    if most is not None:
        count = await session.scalar(without_candidates_query(company_id))

        if count >= most:
            raise OverLimit(count)

    session.add(interview)
    await session.flush()

    return interview


async def create_from_template(
    session: AsyncSession, company_id, set_id, title: str, language: str, seconds: int
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

    session.add(interview)
    await session.flush()

    return interview


async def get_by_link(session: AsyncSession, token: str) -> Interview | None:
    query = select(Interview).where(Interview.link_token == token)

    return await session.scalar(query)


async def set_link(session: AsyncSession, interview_id, token: str | None) -> None:
    await session.execute(
        update(Interview).where(Interview.id == interview_id).values(link_token=token)
    )


async def get(session: AsyncSession, interview_id) -> Interview | None:
    return await session.get(Interview, interview_id)


async def counts(session: AsyncSession, company_ids: list) -> dict:
    if not company_ids:
        return {}

    query = (
        select(Interview.company_id, func.count())
        .where(Interview.company_id.in_(company_ids))
        .group_by(Interview.company_id)
    )

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


async def without_candidates(session: AsyncSession, company_id) -> int:
    """The company's generated interviews no candidate is invited to (yet, or any more); copies
    of templates cost nothing and aren't counted."""
    return await session.scalar(without_candidates_query(company_id)) or 0


async def list_for_company(
    session: AsyncSession,
    company_id,
    offset: int,
    limit: int,
    since: datetime | None = None,
    after: uuid.UUID | None = None,
    q: str = "",
) -> list[Interview]:
    """Newest first, at most `limit`. With
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

    return list(await session.scalars(query))


async def page_by_id(
    session: AsyncSession, company_id, after: uuid.UUID | None, limit: int
) -> list[Interview]:
    """Up to `limit` of the company's interviews, by id, after `after`: all of them, a page at a
    time (a company's deletion)."""
    query = select(Interview).where(Interview.company_id == company_id)

    if after is not None:
        query = query.where(Interview.id > after)

    return list(await session.scalars(query.order_by(Interview.id).limit(limit)))


async def set_companies(session: AsyncSession, after: uuid.UUID | None, limit: int) -> list[tuple]:
    """Up to `limit` interviews with questions, by id after `after`: (id, set_id, company_id)."""
    query = select(Interview.id, Interview.set_id, Interview.company_id).where(
        Interview.set_id.is_not(None)
    )

    if after is not None:
        query = query.where(Interview.id > after)

    return [tuple(row) for row in await session.execute(query.order_by(Interview.id).limit(limit))]


async def update_settings(session: AsyncSession, interview_id, settings: InterviewSettings) -> None:
    """Saves the settings that were sent; marking the test hired also turns its shareable link
    off, so a job ad left online stops bringing in candidates."""
    values = settings.model_dump(exclude_none=True)

    if not values:
        return

    if settings.hired:
        values["link_token"] = None

    await session.execute(update(Interview).where(Interview.id == interview_id).values(**values))


async def set_topic_limit(
    session: AsyncSession,
    interview_id,
    topic_id: uuid.UUID,
    limit: int,
    allowed: Callable[[dict[str, int]], bool],
) -> bool:
    """Sets the topic's number of questions, when `allowed` takes the new numbers; False, with
    nothing changed, when it doesn't. Locked, so two changes at once both see the other."""
    interview = await session.scalar(
        select(Interview).where(Interview.id == interview_id).with_for_update()
    )
    limits = {**interview.topic_limits, str(topic_id): limit}

    if not allowed(limits):
        return False

    interview.topic_limits = limits

    return True


async def remove(session: AsyncSession, interview_id) -> list[tuple]:
    """Deletes the interview, with the interview.deleted event when one is removed, once its
    invites went a batch at a time (services/batch_deletion.py), and returns (interview id,
    email, status, hold key) of the invites not finished made meanwhile, deleted with it."""
    # Locked first: an invite being saved now is saved before and returned, or waits and
    # then fails, as its interview is gone.
    await session.scalar(select(Interview.id).where(Interview.id == interview_id).with_for_update())
    # Invites made meanwhile: those not finished are returned, the others go with the
    # interview (cascade).
    await guests.announce_deleted(session, CandidateInvite.interview_id == interview_id)
    late = await session.execute(
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
    removed = [tuple(row) for row in late]
    company_id = await session.scalar(
        delete(Interview).where(Interview.id == interview_id).returning(Interview.company_id)
    )

    if company_id is not None:
        add_deleted(session, interview_id, company_id)

    return removed


def add_deleted(session: AsyncSession, interview_id, company_id) -> None:
    """ats removes the deleted interview's job links and candidates; notifications and the api
    forget its candidates."""
    data = {"interview_id": str(interview_id), "company_id": str(company_id)}
    outbox.add(session, INTERVIEW_DELETED, data)
    outbox.add(session, CANDIDATE_INTERVIEW_DELETED, data)


async def set_title(session: AsyncSession, interview_id, title: str) -> None:
    await session.execute(update(Interview).where(Interview.id == interview_id).values(title=title))


async def by_ids(session: AsyncSession, interview_ids: list) -> list[Interview]:
    """The interviews of those ids that still exist."""
    if not interview_ids:
        return []

    return list(await session.scalars(select(Interview).where(Interview.id.in_(interview_ids))))
