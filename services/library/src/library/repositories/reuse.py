import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from library.constants.reuse import MAX_TOPIC_DISTANCE, MIN_REUSE_ANSWERS
from library.constants.sets import Pool, SetKind

# The bank: proven company questions of templates of the level whose topic is close to the new
# one and, for a company's interview, the shared bank's questions (companies' proven questions,
# never the company's own). The same text can sit in several templates; each is offered once,
# from its closest topic. The templates of the level and language are found first
# (ix_sets_kind_level_language), so distances are measured only to their topics, never to every
# company test's.
FIND_SQL = text(
    """
    WITH templates AS MATERIALIZED (
        SELECT id FROM sets WHERE kind = :kind AND level = :level AND language = :language
    ), found AS (
        SELECT q.id, q.text, q.options, qs.answers,
            t.embedding <=> CAST(:embedding AS vector) AS distance
        FROM templates s
        JOIN topics t ON t.set_id = s.id
        JOIN questions q ON q.topic_id = t.id
        JOIN question_stats qs ON qs.question_id = q.id
        WHERE t.embedding <=> CAST(:embedding AS vector) <= :max_distance
            AND q.pool = :pool AND qs.flag IS NULL AND qs.answers >= :min_answers
        UNION ALL
        SELECT b.id, b.text, b.options, 0, b.embedding <=> CAST(:embedding AS vector)
        FROM bank_questions b
        LEFT JOIN questions source ON source.id = b.source_question_id
        WHERE CAST(:company_id AS uuid) IS NOT NULL
            AND b.level = :level AND b.language = :language
            AND b.embedding <=> CAST(:embedding AS vector) <= :max_distance
            AND source.company_id IS DISTINCT FROM CAST(:company_id AS uuid)
    )
    SELECT id, text, options FROM (
        SELECT DISTINCT ON (text) id, text, options, answers, distance
        FROM found
        ORDER BY text, distance
    ) candidates
    ORDER BY distance, answers DESC
    LIMIT :count
    """
)


SAVE_EMBEDDING_SQL = text("UPDATE topics SET embedding = CAST(:embedding AS vector) WHERE id = :id")


def as_vector(embedding: list[float]) -> str:
    return "[" + ",".join(str(value) for value in embedding) + "]"


async def save_embeddings(
    session: AsyncSession,
    topic_ids: list[uuid.UUID],
    embeddings: list[list[float] | None],
) -> None:
    rows = [
        {"id": topic_id, "embedding": as_vector(embedding)}
        for topic_id, embedding in zip(topic_ids, embeddings)
        if embedding is not None
    ]

    # One statement sent for every topic at once (executemany).
    if rows:
        await session.execute(SAVE_EMBEDDING_SQL, rows)


MISSING_SQL = text(
    """
    SELECT t.id, t.title, t.subtopics FROM topics t JOIN sets s ON s.id = t.set_id
    WHERE s.kind IN (:template, :interview) AND t.embedding IS NULL
    ORDER BY t.id
    LIMIT :limit
    """
)


async def missing(session: AsyncSession, limit: int) -> list[tuple[uuid.UUID, str, list[str]]]:
    """Template and company test topics without an embedding: templates copied in by hand, and
    tests saved before their embeddings were kept."""
    params = {"template": SetKind.TEMPLATE, "interview": SetKind.INTERVIEW, "limit": limit}

    rows = await session.execute(MISSING_SQL, params)

    return [tuple(row) for row in rows]


async def save(session: AsyncSession, embeddings: dict[uuid.UUID, list[float]]) -> None:
    await save_embeddings(session, list(embeddings), list(embeddings.values()))


async def find(
    session: AsyncSession,
    embedding: list[float],
    level: str,
    language: str,
    count: int,
    company_id: uuid.UUID | None = None,
) -> list[tuple[uuid.UUID, str, list]]:
    """With `company_id` (a company's interview), the shared bank's questions too."""
    params = {
        "company_id": company_id,
        "embedding": as_vector(embedding),
        "kind": SetKind.TEMPLATE,
        "pool": Pool.COMPANY,
        "level": level,
        "language": language,
        "max_distance": MAX_TOPIC_DISTANCE,
        "min_answers": MIN_REUSE_ANSWERS,
        "count": count,
    }

    return [tuple(row) for row in await session.execute(FIND_SQL, params)]
