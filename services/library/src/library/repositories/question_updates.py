from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from library.constants.sets import OwnerType
from library.models.quality import QuestionRevision, QuestionStats
from library.models.sets import Question, QuestionSet, Topic


def of_companies(model, at, company_ids: list[str], since: datetime, until: datetime):
    """When each of the model's rows came (`at`, between the two times), the company and the
    interview's and the topic's titles, for questions of the companies' interviews."""
    return (
        select(at, QuestionSet.owner_id, QuestionSet.title, Topic.title)
        .select_from(model)
        .join(Question, Question.id == model.question_id)
        .join(Topic, Topic.id == Question.topic_id)
        .join(QuestionSet, QuestionSet.id == Topic.set_id)
        .where(
            QuestionSet.owner_type == OwnerType.COMPANY,
            QuestionSet.owner_id.in_(company_ids),
            at > since,
            at <= until,
        )
    )


def kinds(company_ids: list[str], since: datetime, until: datetime) -> dict:
    """Each kind of update: the questions of the companies' interviews newly flagged, and those
    fixed (replaced as flagged), after `since` and up to `until`, with when each came."""
    flagged = of_companies(QuestionStats, QuestionStats.flag_raised_at, company_ids, since, until)
    fixed = of_companies(
        QuestionRevision, QuestionRevision.replaced_at, company_ids, since, until
    ).where(QuestionRevision.fixed)

    return {
        "question_flagged": (flagged, QuestionStats.flag_raised_at),
        "question_fixed": (fixed, QuestionRevision.replaced_at),
    }


async def between(
    session: AsyncSession, company_ids: list[str], since: datetime, until: datetime, limit: int
) -> list[tuple]:
    """The newest `limit` of each kind (kinds): (kind, at, company id, interview, topic)."""
    found = []

    for kind, (query, at) in kinds(company_ids, since, until).items():
        rows = await session.execute(query.order_by(at.desc()).limit(limit))
        found += [(kind, *row) for row in rows]

    return found


async def counts(
    session: AsyncSession, company_ids: list[str], since: datetime, until: datetime
) -> dict[str, int]:
    """How many of each kind (kinds) there are in all."""
    found = {}

    for kind, (query, _) in kinds(company_ids, since, until).items():
        found[kind] = await session.scalar(select(func.count()).select_from(query.subquery()))

    return found
