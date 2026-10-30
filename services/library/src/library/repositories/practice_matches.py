import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from library.constants.reuse import MAX_TOPIC_DISTANCE
from library.constants.sets import SetKind

# The templates' topics a company's interview matches, for its Discover tab: a template of the
# interview's level whose topic is within MAX_TOPIC_DISTANCE of one of the interview's (the same
# subject, as the question bank measures it). Templates of any language count: the person
# practised the subject, whatever language they chose.
MATCHES_SQL = text(
    """
    SELECT DISTINCT template_topic.id
    FROM sets interview
    JOIN topics topic ON topic.set_id = interview.id
    JOIN sets template ON template.kind = :template AND template.level = interview.level
    JOIN topics template_topic ON template_topic.set_id = template.id
    WHERE interview.id = :set_id AND interview.kind = :interview
        AND topic.embedding IS NOT NULL AND template_topic.embedding IS NOT NULL
        AND template_topic.embedding <=> topic.embedding <= :max_distance
    """
)


async def practice_topics(session: AsyncSession, set_id: uuid.UUID) -> list[uuid.UUID]:
    """The template topics matching the interview set's topics and level; none for a set that
    isn't a company's interview."""
    rows = await session.scalars(
        MATCHES_SQL,
        {
            "set_id": set_id,
            "template": SetKind.TEMPLATE,
            "interview": SetKind.INTERVIEW,
            "max_distance": MAX_TOPIC_DISTANCE,
        },
    )

    return list(rows)
