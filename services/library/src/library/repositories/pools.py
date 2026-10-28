import uuid

from prepza_common.ai.sets import TopicAdditionIn
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, selectinload

from library.constants.sets import Pool
from library.models.sets import Question, Topic


def pool_count(pool: Pool):
    return (
        select(func.count(Question.id))
        .where(Question.topic_id == Topic.id, Question.pool == pool)
        .scalar_subquery()
    )


async def topic_counts(
    session: AsyncSession, template_id: uuid.UUID
) -> list[tuple[Topic, int, int]]:
    """Each topic of a template, in order, with its practice and company question counts."""
    query = (
        select(Topic, pool_count(Pool.PRACTICE), pool_count(Pool.COMPANY))
        .where(Topic.set_id == template_id)
        .order_by(Topic.position)
    )

    return [tuple(row) for row in await session.execute(query)]


async def topics_with_questions(session: AsyncSession, template_id: uuid.UUID) -> list[Topic]:
    """A template's topics, in order, with each question's text and pool."""
    query = (
        select(Topic)
        .where(Topic.set_id == template_id)
        .order_by(Topic.position)
        .options(selectinload(Topic.questions).options(load_only(Question.text, Question.pool)))
    )

    return list(await session.scalars(query))


async def add_questions(
    session: AsyncSession, template_id: uuid.UUID, added: list[TopicAdditionIn]
) -> list[list[uuid.UUID]] | None:
    """Saves new questions after each topic's last, in their pools, all or none; each topic's
    new question ids, in the order given. None when a topic isn't the template's."""
    topic_ids = set(await session.scalars(select(Topic.id).where(Topic.set_id == template_id)))

    if any(topic.topic_id not in topic_ids for topic in added):
        return None

    saved = []
    lasts = dict(
        (
            await session.execute(
                select(Question.topic_id, func.max(Question.position))
                .where(Question.topic_id.in_([topic.topic_id for topic in added]))
                .group_by(Question.topic_id)
            )
        ).all()
    )

    for topic in added:
        last = lasts.get(topic.topic_id)
        pooled = [(Pool.PRACTICE, q) for q in topic.practice] + [
            (Pool.COMPANY, q) for q in topic.company
        ]
        questions = [
            Question(
                topic_id=topic.topic_id,
                position=(last if last is not None else -1) + 1 + index,
                text=question.text,
                options=[option.model_dump() for option in question.options],
                source_question_id=question.source_id,
                pool=pool,
            )
            for index, (pool, question) in enumerate(pooled)
        ]
        session.add_all(questions)
        saved.append(questions)

    await session.flush()
    ids = [[question.id for question in questions] for questions in saved]

    return ids
