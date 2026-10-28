import uuid

from fastapi import HTTPException, status
from prepza_common.ai.sets import PreparationIn

from library.core.db import Session
from library.helpers.sets import new_interview
from library.models.sets import QuestionSet, Topic
from library.repositories import preparations
from library.services.set_saves import save_once


async def create_interview(payload: PreparationIn) -> uuid.UUID:
    """A company's interview, with its topics' embeddings (kept like a template's). A retried
    save from the same generation returns the set it already made."""

    async def create() -> uuid.UUID:
        async with Session.begin() as session:
            embeddings = [topic.embedding for topic in payload.topics]

            return await preparations.add(session, new_interview(payload), embeddings)

    return await save_once(payload.generation_id, create)


async def with_topics(set_id: uuid.UUID) -> tuple[QuestionSet, list[tuple[Topic, int]]] | None:
    """A set and its topics, each with how many questions candidates can be given."""
    async with Session() as session:
        question_set = await preparations.get(session, set_id)

        if question_set is None:
            return None

        return question_set, await preparations.get_topics(session, set_id)


async def rename(set_id: uuid.UUID, title: str) -> None:
    async with Session.begin() as session:
        if await preparations.get(session, set_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Set not found")

        await preparations.set_title(session, set_id, title)


async def delete(set_id: uuid.UUID) -> None:
    """Deletes the set; safe to repeat."""
    async with Session.begin() as session:
        if await preparations.get(session, set_id) is not None:
            await preparations.remove(session, set_id)
