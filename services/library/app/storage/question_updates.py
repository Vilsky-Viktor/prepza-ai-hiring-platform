from datetime import datetime

from sqlalchemy import select

from app.constants.sets import OwnerType
from app.models.quality import QuestionRevision, QuestionStats
from app.models.sets import Question, QuestionSet, Topic
from app.storage.db import Session


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


async def between(company_ids: list[str], since: datetime, until: datetime) -> list[tuple]:
    """Each question of the companies' interviews newly flagged, and each fixed (replaced as
    flagged), after `since` and up to `until`: (kind, at, company id, interview, topic)."""
    flagged = of_companies(QuestionStats, QuestionStats.flag_raised_at, company_ids, since, until)
    fixed = of_companies(
        QuestionRevision, QuestionRevision.replaced_at, company_ids, since, until
    ).where(QuestionRevision.fixed)

    async with Session() as session:
        found = [("question_flagged", *row) for row in await session.execute(flagged)]
        found += [("question_fixed", *row) for row in await session.execute(fixed)]

        return found
