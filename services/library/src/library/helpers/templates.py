import uuid

from library.constants.templates import MIN_INDEXABLE_TOPICS
from library.models.sets import QuestionSet
from library.schemas.templates import TemplateSummary


def is_indexable(topic_count: int, duplicate: bool) -> bool:
    """Whether search engines should index a template's public pages: it covers at least
    MIN_INDEXABLE_TOPICS topics and is the first template of its title in its language (a later
    one with the same title is a near-duplicate of it)."""
    return topic_count >= MIN_INDEXABLE_TOPICS and not duplicate


def summarized(rows: list[QuestionSet], duplicates: set[uuid.UUID]) -> list[TemplateSummary]:
    """Templates as the API lists them, each saying whether its public pages are indexed;
    `duplicates` are the near-duplicates among them (templates.duplicate_ids)."""
    return [
        TemplateSummary.model_validate(row, from_attributes=True).model_copy(
            update={"indexable": is_indexable(row.topic_count, row.id in duplicates)}
        )
        for row in rows
    ]
