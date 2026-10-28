from datetime import datetime

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from companies.constants.invites import InviteStatus
from companies.models.interviews import Interview
from companies.models.invites import CandidateInvite

STEPS = ("started_at", "finished_at", "undelivered_at")


def between(column, since: datetime, until: datetime):
    return and_(column > since, column <= until)


def of_companies(company_ids: list, since: datetime, until: datetime) -> list:
    """The companies' candidates with a step after `since` and up to `until`; erased ones
    aren't among them."""
    return [
        Interview.company_id.in_(company_ids),
        CandidateInvite.status != InviteStatus.DELETED,
        or_(*(between(getattr(CandidateInvite, step), since, until) for step in STEPS)),
    ]


async def changed(
    session: AsyncSession, company_ids: list, since: datetime, until: datetime, limit: int
) -> list[tuple[CandidateInvite, Interview]]:
    """Up to `limit` of the companies' candidates who started, finished or whose invite wasn't
    delivered after `since` and up to `until`, with their interviews, the latest step first: they
    hold the newest `limit` steps."""
    latest = func.greatest(
        *(
            case(
                (
                    between(getattr(CandidateInvite, step), since, until),
                    getattr(CandidateInvite, step),
                )
            )
            for step in STEPS
        )
    )
    query = (
        select(CandidateInvite, Interview)
        .join(Interview, Interview.id == CandidateInvite.interview_id)
        .where(*of_companies(company_ids, since, until))
        .order_by(latest.desc(), CandidateInvite.id)
        .limit(limit)
    )

    return list(await session.execute(query))


async def counts(
    session: AsyncSession, company_ids: list, since: datetime, until: datetime
) -> tuple[int, ...]:
    """How many of the companies' candidates started, finished, finished and passed (a grade at
    the interview's pass mark), and weren't delivered after `since` and up to `until`."""
    finished = between(CandidateInvite.finished_at, since, until)
    query = (
        select(
            func.count().filter(between(CandidateInvite.started_at, since, until)),
            func.count().filter(finished),
            func.count().filter(finished, CandidateInvite.grade >= Interview.pass_mark),
            func.count().filter(between(CandidateInvite.undelivered_at, since, until)),
        )
        .select_from(CandidateInvite)
        .join(Interview, Interview.id == CandidateInvite.interview_id)
        .where(*of_companies(company_ids, since, until))
    )

    return tuple((await session.execute(query)).one())
