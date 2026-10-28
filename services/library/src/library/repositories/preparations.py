import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from library.constants.sets import Pool
from library.models.sets import Question, QuestionSet, Topic
from library.repositories import reuse


def served():
    """A question candidates can be given: not a copy of a practice question, shown with its
    answer in free practice. Copies are only ever made of company questions; this leaves out
    copies made before the pools of questions that were revealed since (migration 0027)."""
    source = aliased(Question)

    return ~(
        select(source.id)
        .where(source.id == Question.source_question_id, source.pool == Pool.PRACTICE)
        .exists()
    )


def set_query(question_id: uuid.UUID):
    return (
        select(QuestionSet)
        .join(Topic, Topic.set_id == QuestionSet.id)
        .join(Question, Question.topic_id == Topic.id)
        .where(Question.id == question_id)
    )


def topic_query(question_id: uuid.UUID):
    return (
        select(Topic.title)
        .join(Question, Question.topic_id == Topic.id)
        .where(Question.id == question_id)
    )


async def find_by_generation(session: AsyncSession, generation_id: uuid.UUID) -> uuid.UUID | None:
    query = select(QuestionSet.id).where(QuestionSet.generation_id == generation_id)

    return await session.scalar(query)


async def add(
    session: AsyncSession, question_set: QuestionSet, embeddings: list[list[float] | None]
) -> uuid.UUID:
    """Saves a new set with its topics and questions, and each topic's embedding (in topic order)
    for the question bank; its id."""
    session.add(question_set)
    await session.flush()
    await reuse.save_embeddings(session, [topic.id for topic in question_set.topics], embeddings)

    return question_set.id


async def get_content(session: AsyncSession, set_id: uuid.UUID) -> QuestionSet | None:
    """A set with every topic and the questions candidates can be given (served), for starting
    candidate sessions."""
    query = (
        select(QuestionSet)
        .where(QuestionSet.id == set_id)
        .options(selectinload(QuestionSet.topics).selectinload(Topic.questions.and_(served())))
    )

    return await session.scalar(query)


async def get(session: AsyncSession, set_id: uuid.UUID) -> QuestionSet | None:
    return await session.get(QuestionSet, set_id)


async def get_topics(session: AsyncSession, set_id: uuid.UUID) -> list[tuple[Topic, int]]:
    """Topics with counts of the questions candidates can be given, without loading them."""
    question_count = (
        select(func.count(Question.id))
        .where(Question.topic_id == Topic.id, served())
        .scalar_subquery()
    )
    query = select(Topic, question_count).where(Topic.set_id == set_id).order_by(Topic.position)

    return [tuple(row) for row in await session.execute(query)]


async def get_topic_with_question_texts(
    session: AsyncSession,
    topic_id: uuid.UUID,
) -> tuple[QuestionSet, Topic] | None:
    """A topic's set and its questions, with only what managing them needs."""
    query = (
        select(QuestionSet, Topic)
        .join(Topic, Topic.set_id == QuestionSet.id)
        .where(Topic.id == topic_id)
        .options(
            selectinload(Topic.questions).load_only(Question.id, Question.text, Question.options)
        )
    )

    row = (await session.execute(query)).first()

    return tuple(row) if row else None


async def get_for_question(session: AsyncSession, question_id: uuid.UUID) -> QuestionSet | None:
    return await session.scalar(set_query(question_id))


async def topic_of_question(session: AsyncSession, question_id: uuid.UUID) -> str | None:
    """The title of the topic the question is in."""
    return await session.scalar(topic_query(question_id))


async def get_question_context(
    session: AsyncSession,
    question_id: uuid.UUID,
) -> tuple[QuestionSet, Topic] | None:
    """The question's set and topic, with every question of that topic."""
    query = (
        select(QuestionSet, Topic)
        .join(Topic, Topic.set_id == QuestionSet.id)
        .join(Question, Question.topic_id == Topic.id)
        .where(Question.id == question_id)
        .options(selectinload(Topic.questions))
    )

    row = (await session.execute(query)).first()

    return tuple(row) if row else None


async def question(session: AsyncSession, question_id: uuid.UUID) -> Question | None:
    return await session.get(Question, question_id)


async def set_content(
    session: AsyncSession, question_id: uuid.UUID, text: str, options: list[dict]
) -> None:
    """New content in the question's slot; archive the old one first (quality.archive)."""
    await session.execute(
        update(Question).where(Question.id == question_id).values(text=text, options=options)
    )


async def set_title(session: AsyncSession, set_id: uuid.UUID, title: str) -> None:
    await session.execute(update(QuestionSet).where(QuestionSet.id == set_id).values(title=title))


async def remove(session: AsyncSession, set_id: uuid.UUID) -> None:
    """Deletes the set; its topics, questions, feedback, invites and joins cascade with it."""
    await session.execute(delete(QuestionSet).where(QuestionSet.id == set_id))
