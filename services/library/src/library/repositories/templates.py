import uuid

from prepza_common.ai.sets import PreparationIn
from sqlalchemy import Text, and_, cast, func, or_, select, text
from sqlalchemy.orm import aliased, selectinload

from library.constants.reuse import MIN_COPY_QUESTIONS
from library.constants.sets import PLATFORM_OWNER, OwnerType, Pool, SetKind
from library.core.db import Session
from library.helpers.pools import assign_pools
from library.helpers.search import escape_like
from library.helpers.slugs import slugify, unique_slug
from library.models.sets import Question, QuestionSet, Topic
from library.repositories import reuse
from library.repositories.preparations import new_topics

COPY_EMBEDDING_SQL = text(
    "UPDATE topics SET embedding = (SELECT embedding FROM topics WHERE id = :source) WHERE id = :id"
)


async def create_template(payload: PreparationIn, share: float) -> uuid.UUID:
    """An admin's template, with its topics' embeddings for the question bank; `share` of each
    topic's practice questions are multi-answer (assign_pools)."""
    question_set = QuestionSet(
        generation_id=payload.generation_id,
        kind=SetKind.TEMPLATE,
        owner_type=OwnerType.PLATFORM,
        owner_id=PLATFORM_OWNER,
        title=payload.title,
        source_text=payload.source_text,
        level=payload.level,
        language=payload.language,
        requirements=payload.requirements,
        topics=new_topics(payload),
        topic_count=len(payload.topics),
    )

    for topic in question_set.topics:
        assign_pools(topic.questions, share)

    async with Session() as session:
        question_set.slug = await free_slug(session, slugify(payload.title))
        session.add(question_set)
        await session.flush()
        await reuse.save_embeddings(
            session,
            [topic.id for topic in question_set.topics],
            [topic.embedding for topic in payload.topics],
        )
        await session.commit()

    return question_set.id


async def free_slug(session, base: str) -> str:
    """`base`, or it with the first free "-2", "-3"… A slug holds only letters, digits and "-",
    so it needs no escaping in LIKE."""
    query = select(QuestionSet.slug).where(
        or_(QuestionSet.slug == base, QuestionSet.slug.like(f"{base}-%"))
    )

    return unique_slug(base, set(await session.scalars(query)))


async def get_by_slug(slug: str) -> QuestionSet | None:
    query = select(QuestionSet).where(QuestionSet.slug == slug)

    async with Session() as session:
        return await session.scalar(query)


async def duplicate_ids(ids: list[uuid.UUID]) -> set[uuid.UUID]:
    """The templates among `ids` with an older template of the same title (any case) and
    language: near-duplicates of it. Of two made at once, the one with the smaller id is older."""
    older = aliased(QuestionSet)
    has_older = (
        select(older.id)
        .where(
            older.kind == SetKind.TEMPLATE,
            func.lower(older.title) == func.lower(QuestionSet.title),
            older.language == QuestionSet.language,
            or_(
                older.created_at < QuestionSet.created_at,
                and_(older.created_at == QuestionSet.created_at, older.id < QuestionSet.id),
            ),
        )
        .exists()
    )
    query = select(QuestionSet.id).where(QuestionSet.id.in_(ids), has_older)

    async with Session() as session:
        return set(await session.scalars(query))


async def sample_questions(template_id: uuid.UUID, limit: int) -> list[tuple[Question, str]]:
    """Up to `limit` practice questions with their topic's title, spread across topics: each
    topic's first, in topic order, then each one's second, and so on."""
    rank = (
        func.row_number().over(partition_by=Question.topic_id, order_by=Question.position)
    ).label("rank")
    ranked = (
        select(Question.id, rank, Topic.position.label("topic_position"))
        .join(Topic, Topic.id == Question.topic_id)
        .where(Topic.set_id == template_id, Question.pool == Pool.PRACTICE)
        .subquery()
    )
    query = (
        select(Question, Topic.title)
        .join(ranked, ranked.c.id == Question.id)
        .join(Topic, Topic.id == Question.topic_id)
        .order_by(ranked.c.rank, ranked.c.topic_position)
        .limit(limit)
    )

    async with Session() as session:
        return [(question, title) for question, title in await session.execute(query)]


async def copy_template(template_id: uuid.UUID, company_id: str) -> QuestionSet | None:
    """A company's own test made from a template, with no generation: its topics with their
    company questions and embeddings, each question remembering its original so its answers
    count there too. Topics with fewer than MIN_COPY_QUESTIONS company questions are skipped. None when there's no such template, or none of its topics is left."""
    query = (
        select(QuestionSet)
        .where(QuestionSet.id == template_id, QuestionSet.kind == SetKind.TEMPLATE)
        .options(selectinload(QuestionSet.topics).selectinload(Topic.questions))
    )

    async with Session() as session:
        template = await session.scalar(query)

        if template is None:
            return None

        kept = []

        for topic in template.topics:
            company = [q for q in topic.questions if q.pool == Pool.COMPANY]

            if len(company) >= MIN_COPY_QUESTIONS:
                kept.append((topic, company))

        if not kept:
            return None

        copy = QuestionSet(
            kind=SetKind.INTERVIEW,
            owner_type=OwnerType.COMPANY,
            owner_id=company_id,
            title=template.title,
            source_text=template.source_text,
            level=template.level,
            language=template.language,
            requirements=template.requirements,
            topic_count=len(kept),
            topics=[
                Topic(
                    position=position,
                    title=topic.title,
                    subtopics=topic.subtopics,
                    questions=[
                        Question(
                            position=q.position,
                            text=q.text,
                            options=q.options,
                            source_question_id=q.id,
                        )
                        for q in company
                    ],
                )
                for position, (topic, company) in enumerate(kept)
            ],
        )
        session.add(copy)
        await session.flush()

        copied = [{"id": new.id, "source": topic.id} for new, (topic, _) in zip(copy.topics, kept)]

        if copied:
            await session.execute(COPY_EMBEDDING_SQL, copied)

        await session.commit()

        return copy


async def list_templates(
    q: str,
    level: str | None,
    languages: list[str],
    offset: int,
    limit: int,
    copyable: bool = False,
) -> list[QuestionSet]:
    """Newest first; `q` matches anywhere in the title, a topic's title or a subtopic, and no
    languages means every one. `copyable` keeps only the templates copy_template can copy: with
    a topic that has at least MIN_COPY_QUESTIONS company questions."""
    filters = [QuestionSet.kind == SetKind.TEMPLATE]

    if copyable:
        full_topics = (
            select(Question.topic_id)
            .join(Topic, Topic.id == Question.topic_id)
            .where(Topic.set_id == QuestionSet.id, Question.pool == Pool.COMPANY)
            .group_by(Question.topic_id)
            .having(func.count() >= MIN_COPY_QUESTIONS)
            .exists()
        )
        filters.append(full_topics)

    if q:
        pattern = f"%{escape_like(q)}%"
        in_topics = (
            select(Topic.id)
            .where(
                Topic.set_id == QuestionSet.id,
                or_(
                    Topic.title.ilike(pattern, escape="\\"),
                    cast(Topic.subtopics, Text).ilike(pattern, escape="\\"),
                ),
            )
            .exists()
        )
        filters.append(or_(QuestionSet.title.ilike(pattern, escape="\\"), in_topics))

    if level:
        filters.append(QuestionSet.level == level)

    if languages:
        filters.append(QuestionSet.language.in_(languages))

    query = (
        select(QuestionSet)
        .where(*filters)
        .order_by(QuestionSet.created_at.desc(), QuestionSet.id)
        .offset(offset)
        .limit(limit)
    )

    async with Session() as session:
        return list(await session.scalars(query))
