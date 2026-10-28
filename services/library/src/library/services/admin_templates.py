"""The superadmin's templates (docs/features/admin-zone.md, Templates)."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from library.constants.sets import SetKind
from library.core.db import Session
from library.helpers.templates import summarized
from library.models.sets import QuestionSet, Topic
from library.repositories import pools, preparations, templates
from library.schemas.templates import TemplateSummary


async def template(session: AsyncSession, template_id: uuid.UUID) -> QuestionSet:
    """The template; 404 when there's none."""
    found = await preparations.get(session, template_id)

    if found is None or found.kind != SetKind.TEMPLATE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")

    return found


async def with_pools(
    template_id: uuid.UUID,
) -> tuple[TemplateSummary, list[tuple[Topic, int, int]]]:
    """The template with its topics' practice and company question counts."""
    async with Session() as session:
        found = await template(session, template_id)
        topics = await pools.topic_counts(session, template_id)
        duplicates = await templates.duplicate_ids(session, [template_id])

    return summarized([found], duplicates)[0], topics


async def rename(template_id: uuid.UUID, title: str) -> None:
    async with Session.begin() as session:
        await template(session, template_id)
        await preparations.set_title(session, template_id, title)


async def delete(template_id: uuid.UUID) -> None:
    async with Session.begin() as session:
        await template(session, template_id)
        await preparations.remove(session, template_id)
