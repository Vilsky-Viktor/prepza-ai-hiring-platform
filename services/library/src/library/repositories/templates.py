import uuid

from sqlalchemy import Text, and_, cast, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from library.constants.reuse import MIN_COPY_QUESTIONS
from library.constants.sets import Pool, SetKind
from library.helpers.search import escape_like
from library.helpers.slugs import unique_slug
from library.models.sets import Question, QuestionSet, Topic

COPY_EMBEDDING_SQL = text(
    "UPDATE topics SET embedding = (SELECT embedding FROM topics WHERE id = :source) WHERE id = :id"
)


async def free_slug(session: AsyncSession, base: str) -> str:
    """`base`, or it with the first free "-2", "-3"… A slug holds only letters, digits and "-",
    so it needs no escaping in LIKE."""
    query = select(QuestionSet.slug).where(
        or_(QuestionSet.slug == base, QuestionSet.slug.like(f"{base}-%"))
    )

    return unique_slug(base, set(await session.scalars(query)))


async def get_by_slug(session: AsyncSession, slug: str) -> QuestionSet | None:
    query = select(QuestionSet).where(QuestionSet.slug == slug)

    return await session.scalar(query)


async def duplicate_ids(session: AsyncSession, ids: list[uuid.UUID]) -> set[uuid.UUID]:
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

    return set(await session.scalars(query))


async def sample_questions(
    session: AsyncSession, template_id: uuid.UUID, limit: int
) -> list[tuple[Question, str]]:
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

    return [(question, title) for question, title in await session.execute(query)]


async def with_questions(session: AsyncSession, template_id: uuid.UUID) -> QuestionSet | None:
    """A template with its topics and their questions; None when there's no such template."""
    query = (
        select(QuestionSet)
        .where(QuestionSet.id == template_id, QuestionSet.kind == SetKind.TEMPLATE)
        .options(selectinload(QuestionSet.topics).selectinload(Topic.questions))
    )

    return await session.scalar(query)


async def add_copy(session: AsyncSession, copy: QuestionSet, sources: list[uuid.UUID]) -> None:
    """Saves a test copied from a template; its topics get the embeddings of the template's
    topics they came from (`sources`, in topic order)."""
    session.add(copy)
    await session.flush()
    copied = [{"id": new.id, "source": source} for new, source in zip(copy.topics, sources)]

    if copied:
        await session.execute(COPY_EMBEDDING_SQL, copied)


async def list_templates(
    session: AsyncSession,
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

    return list(await session.scalars(query))
