import uuid

from fastapi import HTTPException, status
from prepza_common.ai.multi_answer import multi_share
from prepza_common.ai.sets import PreparationIn

from library.constants.sets import SetKind
from library.core.db import Session
from library.helpers.sets import copied, new_template
from library.helpers.slugs import slugify
from library.helpers.templates import summarized
from library.integrations.redis import get_redis
from library.models.sets import Question, QuestionSet, Topic
from library.repositories import preparations, templates
from library.schemas.templates import TemplateSummary
from library.services.set_saves import save_once


async def create(payload: PreparationIn) -> uuid.UUID:
    """An admin's template, with its practice questions given today's share of multi-answer
    ones. A retried save from the same generation returns the template it already made."""

    async def save() -> uuid.UUID:
        return await save_template(payload, await multi_share(get_redis()))

    return await save_once(payload.generation_id, save)


async def save_template(payload: PreparationIn, share: float) -> uuid.UUID:
    """Saves the template with its topics' embeddings for the question bank; `share` of each
    topic's practice questions are multi-answer (assign_pools)."""
    async with Session.begin() as session:
        template = new_template(payload, share)
        template.slug = await templates.free_slug(session, slugify(payload.title))
        embeddings = [topic.embedding for topic in payload.topics]

        return await preparations.add(session, template, embeddings)


async def copy_template(template_id: uuid.UUID, company_id: str) -> QuestionSet:
    """A company's own test made from a template, with no generation (helpers/sets.copied);
    not found when there's no such template, or none of its topics has enough company
    questions."""
    async with Session.begin() as session:
        template = await templates.with_questions(session, template_id)
        made = copied(template, company_id) if template is not None else None

        if made is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")

        await templates.add_copy(session, *made)

    return made[0]


async def listed(
    q: str,
    level: str | None,
    languages: list[str],
    offset: int,
    limit: int,
    copyable: bool = False,
) -> list[TemplateSummary]:
    """Templates as the API lists them (templates.list_templates), each saying whether its
    public pages are indexed."""
    async with Session() as session:
        rows = await templates.list_templates(session, q, level, languages, offset, limit, copyable)
        duplicates = await templates.duplicate_ids(session, [row.id for row in rows])

    return summarized(rows, duplicates)


async def find(session, key: str) -> QuestionSet:
    """A template by its id or its slug; 404 when there's none."""
    try:
        template_id = uuid.UUID(key)
    except ValueError:
        template_id = None

    if template_id is None:
        template = await templates.get_by_slug(session, key)
    else:
        template = await preparations.get(session, template_id)

    if template is None or template.kind != SetKind.TEMPLATE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")

    return template


async def with_topics(key: str) -> tuple[TemplateSummary, list[tuple[Topic, int]]]:
    """A template, by its id or slug, with its topics and their question counts."""
    async with Session() as session:
        template = await find(session, key)
        topics = await preparations.get_topics(session, template.id)
        duplicates = await templates.duplicate_ids(session, [template.id])

    return summarized([template], duplicates)[0], topics


async def sample(key: str, limit: int) -> list[tuple[Question, str]]:
    """Up to `limit` of the template's practice questions, with their topic's title."""
    async with Session() as session:
        template = await find(session, key)

        return await templates.sample_questions(session, template.id, limit)
