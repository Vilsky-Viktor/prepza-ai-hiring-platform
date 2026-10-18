import uuid

from prepza_common import outbox
from prepza_common.notifications import NOTIFICATION_REQUESTED, NotificationKind
from prepza_common.sets import PreparationIn
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import aliased, selectinload

from app.constants.sets import OwnerType, Pool, SetKind
from app.helpers.notifications import question_notification
from app.models.outbox import OutboxEvent
from app.models.quality import QuestionStats
from app.models.sets import Question, QuestionSet, Topic
from app.storage import quality, reuse
from app.storage.db import Session


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


def new_topics(preparation: PreparationIn) -> list[Topic]:
    """The topics and questions of a generated set, ready to save."""
    return [
        Topic(
            position=ti,
            title=topic.title,
            subtopics=topic.subtopics,
            questions=[
                Question(
                    position=qi,
                    text=question.text,
                    options=[option.model_dump() for option in question.options],
                    source_question_id=question.source_id,
                )
                for qi, question in enumerate(topic.questions)
            ],
        )
        for ti, topic in enumerate(preparation.topics)
    ]


async def find_by_generation(generation_id: uuid.UUID) -> uuid.UUID | None:
    query = select(QuestionSet.id).where(QuestionSet.generation_id == generation_id)

    async with Session() as session:
        return await session.scalar(query)


async def create_interview(payload: PreparationIn) -> uuid.UUID:
    """Company interviews are always private. Their topics' embeddings are kept, like a
    template's."""
    question_set = QuestionSet(
        generation_id=payload.generation_id,
        kind=SetKind.INTERVIEW,
        owner_type=OwnerType.COMPANY,
        owner_id=payload.owner_uid,
        title=payload.title,
        source_text=payload.source_text,
        level=payload.level,
        language=payload.language,
        requirements=payload.requirements,
        topics=new_topics(payload),
        topic_count=len(payload.topics),
    )

    async with Session() as session:
        session.add(question_set)
        await session.flush()
        await reuse.save_embeddings(
            session,
            [topic.id for topic in question_set.topics],
            [topic.embedding for topic in payload.topics],
        )
        await session.commit()

    return question_set.id


async def get_content(set_id: uuid.UUID) -> QuestionSet | None:
    """A set with every topic and the questions candidates can be given (served), for starting
    candidate sessions."""
    query = (
        select(QuestionSet)
        .where(QuestionSet.id == set_id)
        .options(selectinload(QuestionSet.topics).selectinload(Topic.questions.and_(served())))
    )

    async with Session() as session:
        return await session.scalar(query)


async def get(set_id: uuid.UUID) -> QuestionSet | None:
    async with Session() as session:
        return await session.get(QuestionSet, set_id)


async def get_topics(set_id: uuid.UUID) -> list[tuple[Topic, int]]:
    """Topics with counts of the questions candidates can be given, without loading them."""
    question_count = (
        select(func.count(Question.id))
        .where(Question.topic_id == Topic.id, served())
        .scalar_subquery()
    )
    query = select(Topic, question_count).where(Topic.set_id == set_id).order_by(Topic.position)

    async with Session() as session:
        return [tuple(row) for row in await session.execute(query)]


async def get_topic_with_question_texts(
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

    async with Session() as session:
        row = (await session.execute(query)).first()

        return tuple(row) if row else None


def _set_of_question(question_id: uuid.UUID):
    return (
        select(QuestionSet)
        .join(Topic, Topic.set_id == QuestionSet.id)
        .join(Question, Question.topic_id == Topic.id)
        .where(Question.id == question_id)
    )


async def get_for_question(question_id: uuid.UUID) -> QuestionSet | None:
    async with Session() as session:
        return await session.scalar(_set_of_question(question_id))


def _topic_of_question(question_id: uuid.UUID):
    return (
        select(Topic.title)
        .join(Question, Question.topic_id == Topic.id)
        .where(Question.id == question_id)
    )


async def topic_of_question(question_id: uuid.UUID) -> str | None:
    """The title of the topic the question is in."""
    async with Session() as session:
        return await session.scalar(_topic_of_question(question_id))


async def get_question_context(
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

    async with Session() as session:
        row = (await session.execute(query)).first()

        return tuple(row) if row else None


async def unchanged_copies(session, question_id: uuid.UUID) -> list[uuid.UUID]:
    """The copies of a bank question in companies' tests that still hold its content: not one a
    company changed, nor one fixed on its own."""
    original = aliased(Question)
    query = (
        select(Question.id)
        .join(original, original.id == Question.source_question_id)
        .where(
            original.id == question_id,
            Question.text == original.text,
            Question.options == original.options,
        )
    )

    return list(await session.scalars(query))


async def replace_question(question_id: uuid.UUID, text: str, options: list[dict]) -> None:
    """New content in the same slot, for candidates who start after it. The old content and its
    feedback are kept as a revision.

    Replacing a flagged question fixes it, and its set's owner hears of that. A fixed bank
    question fixes its unchanged copies in companies' tests too, and each company hears of it.
    """
    async with Session() as session:
        flagged = await session.scalar(
            select(QuestionStats.flag).where(QuestionStats.question_id == question_id)
        )
        fixed = [question_id]

        if flagged is not None:
            fixed += await unchanged_copies(session, question_id)

        for each in fixed:
            await quality.archive(session, each, fixed=flagged is not None)

        await session.execute(
            update(Question).where(Question.id.in_(fixed)).values(text=text, options=options)
        )

        if flagged is not None:
            for each in fixed:
                question_set = await session.scalar(_set_of_question(each))
                topic = await session.scalar(_topic_of_question(each))
                outbox.add(
                    session,
                    OutboxEvent,
                    NOTIFICATION_REQUESTED,
                    question_notification(question_set, topic, NotificationKind.QUESTION_FIXED),
                )

        await session.commit()


async def set_title(set_id: uuid.UUID, title: str) -> None:
    async with Session() as session:
        await session.execute(
            update(QuestionSet).where(QuestionSet.id == set_id).values(title=title)
        )
        await session.commit()


async def remove(set_id: uuid.UUID) -> None:
    """Deletes the set; its topics, questions, feedback, invites and joins cascade with it."""
    async with Session() as session:
        await session.execute(delete(QuestionSet).where(QuestionSet.id == set_id))
        await session.commit()
