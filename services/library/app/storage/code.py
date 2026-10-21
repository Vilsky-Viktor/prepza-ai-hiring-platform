import uuid

from sqlalchemy import text

from app.constants.code import UNTAGGED_FENCE
from app.storage.db import Session

# A question whose first fence, which always opens its example, is :fence ("```" then a new line
# for one without a language). A closing fence followed by more text looks the same ("```" then
# a new line), so only the first counts.
FIRST_FENCE = "strpos(text, '```') > 0 AND strpos(text, '```') = strpos(text, :fence)"
LISTED_SQL = text(
    f"""
    SELECT id, text FROM questions WHERE {FIRST_FENCE} AND (CAST(:after AS uuid) IS NULL OR id > :after)
    ORDER BY id
    LIMIT :limit
    """
)
# The first fence gets the language; a question tagged meanwhile is left as it is.
TAG_SQL = text(
    f"""
    UPDATE questions SET text = overlay(text placing :tagged from strpos(text, :fence) for :length)
    WHERE id = :id AND {FIRST_FENCE}
    """
)


async def untagged(
    limit: int, fence: str = UNTAGGED_FENCE, after: uuid.UUID | None = None
) -> list[tuple[uuid.UUID, str]]:
    """Questions whose example opens with `fence` (by default, without a language; the first
    example, for a question with two), in id order after `after`."""
    async with Session() as session:
        rows = await session.execute(LISTED_SQL, {"fence": fence, "after": after, "limit": limit})

        return [tuple(row) for row in rows]


async def tag(languages: dict[uuid.UUID, str], fence: str = UNTAGGED_FENCE) -> None:
    """Each question's example, opening with `fence`, gets its language."""
    rows = [
        {"id": question_id, "fence": fence, "tagged": f"```{language}\n", "length": len(fence)}
        for question_id, language in languages.items()
    ]

    if not rows:
        return

    # One statement sent for every question at once (executemany).
    async with Session() as session:
        await session.execute(TAG_SQL, rows)
        await session.commit()
