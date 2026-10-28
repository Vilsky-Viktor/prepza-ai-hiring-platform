"""For generation: adding questions to a template's topics, a top-up or a superadmin's addition
(docs/features/admin-zone.md, Templates)."""

import uuid

from fastapi import HTTPException, status
from prepza_common.ai.sets import TopicAdditionIn

from library.core.db import Session
from library.models.sets import QuestionSet, Topic
from library.repositories import pools
from library.services.admin_templates import template


async def context(template_id: uuid.UUID) -> tuple[QuestionSet, list[Topic]]:
    """The template with its topics, each with every question's text and pool."""
    async with Session() as session:
        found = await template(session, template_id)

        return found, await pools.topics_with_questions(session, template_id)


async def add(template_id: uuid.UUID, added: list[TopicAdditionIn]) -> list[list[uuid.UUID]]:
    """Saves the new questions of every topic at once, all or none; each topic's new question
    ids."""
    async with Session.begin() as session:
        await template(session, template_id)
        saved = await pools.add_questions(session, template_id, added)

        if saved is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Topic not found")

        return saved
